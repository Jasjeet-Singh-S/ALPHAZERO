import numpy as np
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
from random import shuffle

torch.manual_seed(0)

class ResNet(nn.Module):
    """"
    Resnet neural network class
    
    ### Parameters: 
            - game: the class of game we want the model to train on 
            - num_resBlocks (int)
            - num_hidden
            - device
            
    ### Returns:
            - policy (torch.tensor([batch_size, action_size])): batched up policies, of action scores
            - value (torch.tensor([batch_size, 1])): value of a state in the batched state 
    """
    def __init__(self, game, num_resBlocks, num_hidden, device):
        super().__init__()
        
        self.device = device
        self.startBlock = nn.Sequential(
            nn.Conv2d(3, num_hidden, kernel_size=3, padding=1),
            nn.BatchNorm2d(num_hidden),
            nn.ReLU(),
        )
        
        self.backBone = nn.ModuleList(
            [ResBlock(num_hidden) for i in range(num_resBlocks)]
        )
        
        self.policyHead = nn.Sequential(
            nn.Conv2d(num_hidden, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(32*game.row_count*game.column_count, game.action_size)
        )
        
        self.valueHead = nn.Sequential(
            nn.Conv2d(num_hidden,  3, kernel_size=3, padding=1),
            nn.BatchNorm2d(3),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(3*game.row_count*game.column_count, 1),
            nn.Tanh()
        )
        self.to(device)
        
    def forward(self, x):
        x = self.startBlock(x)
        for resBlock in self.backBone:
            x = resBlock(x)
        policy = self.policyHead(x)
        value = self.valueHead(x)
        return policy, value
        

class ResBlock(nn.Module):
    def __init__(self, num_hidden):
        super().__init__()
        self.conv1 = nn.Conv2d(num_hidden, num_hidden, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(num_hidden)
        self.conv2 = nn.Conv2d(num_hidden, num_hidden, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(num_hidden)
        
    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        x += residual
        x = F.relu(x)
        return x
    

class Node:
    def __init__(self, game, args, state, parent=None, action_taken=None, prior=0, visit_count=0):
        """initializes the Node class"""
        self.game = game 
        self.args = args
        self.state = state
        self.parent = parent
        self.action_taken = action_taken
        self.prior = prior
        
        self.children = []
        
        self.visit_count = visit_count
        self.value_sum = 0
        
    def is_fully_expanded(self):
        """checks if all states possible from a node (except that leaf/terminal node) have been visited or not"""
        return len(self.children) > 0
    
    def select(self):
        """determines which node to explore next using the UCB values of the nodes."""
        best_child = None
        best_ucb = -np.inf
        
        for child in self.children:
            ucb = self.get_ucb(child)
            if ucb>best_ucb:
                best_child = child 
                best_ucb = ucb
            
        return best_child
    
    def get_ucb(self, child: 'Node'):
        """
            calculates the average UCB value normalised to the range [0,1] and inverted so that it is from the perspective of the player who is about to make a move (and not the one who just made the move)
            
            ### Parameters:
                    - child: child node of the current node
                    
            ### Returns:
                    - UCB value
        """
        if child.visit_count==0:
            q_value=0
        else:
            q_value = 1 - ((child.value_sum/child.visit_count) + 1) / 2  # what teh sigma. author says its possible to have negative value sum from -1 to 1 so we add one and divide by 2 so this turns into a probability and we subtract it all from 1 because child is of antagonist whereas parent which actually usues the UCB is of the protagonist
        return q_value + self.args['C'] * (math.sqrt(self.visit_count/(child.visit_count+1))) * child.prior
    
    def expand(self, policy):
        """creates a new node for a valid move in expandable_moves()"""
        for action , prob in enumerate(policy):
            if prob>0:
                child_state = self.state.copy()
                child_state = self.game.get_next_state(child_state, action, 1)
                child_state = self.game.change_perspective(child_state, player=-1)
                
                child = Node(self.game, self.args, child_state, self, action, prob)
                self.children.append(child)
        return child
            
    def backpropagate(self, value):
        """for updating the value estimates of the nodes in the search tree.

        ### Parameters:
                - value (int): 1 for win, 0 for draw, -1 for loss
        """
        self.value_sum += value
        self.visit_count += 1
        
        value = self.game.get_opponent_value(value)
        if self.parent is not None :
            self.parent.backpropagate(value)
            
            
class MCTSParallel:  # This is not really parallel MCTS, more like batched MCTS. Not truly parallel as we are using a for loop for multiple games, maybe we can improve on that later. 
    def __init__(self, game, args, model:ResNet):
        self.game = game
        self.args = args
        self.model = model
    
    @torch.no_grad()  # basically the same as `with torch.no_grad():`
    def search(self, states, spGames):
        """
        Performs Monte Carlo Tree Search (MCTS) simulations in parallel for a batch of game states.

        This function iterates through a specified number of searches, selecting, expanding,
        evaluating, and backpropagating values to improve policy and value estimates for
        the given game states.

        Parameters:
            states (np.array): A NumPy array representing a batch of game states.
                Shape: (batch_size, row_count, column_count)
            spGames (list[SPG]): A list of SPG (Self-Play Game) objects, each containing
                the game state, MCTS tree, and other game-related information for a
                game being played in parallel.

        Returns:
            None. The function modifies the MCTS trees within the spGames objects in place.
        """
        
        # explanation of the function is as follows:
        """this function takes a node, treats it as root node, ie temporarily discards all nodes above it, 
        then expands on the node (one level in one iteration) and picks the best child (if the node is fully expanded)
        in that same iteration and continues till the leaf root node is reached and backpropagate. There 
        are 2 triggerts for backpropagation
        
        Backpropagation is triggered only after a node has been evaluated. This happens in these two scenarios:
            - Terminal Node: If the selected node is a terminal node (win, loss, or draw), the game outcome is used as the evaluation value, and backpropagation occurs.
            - Non-Fully Expanded Node: If the selected node is not fully expanded, it is expanded, the neural network evaluates the new node, and then backpropagation occurs.
        """
        policy, _ = self.model(  # the blank wouldve been policy but we dont need it 
                torch.tensor(self.game.get_encoded_state(states), device=self.model.device)  # we no longer need to call unsqueeze here because we now have a batch
            )
        policy = torch.softmax(policy, axis=1).cpu().numpy()  # again we dont squeeze here because now we need the batches
        
        policy = (1-self.args['dirichlet_epsilon'])*policy + self.args['dirichlet_epsilon']*np.random.dirichlet([self.args['dirichlet_alpha']] * self.game.action_size, size=policy.shape[0])  # weve speicfied the sahpe of noise has to be equal to shape of policy with shape attribute
        
        for i, spg in enumerate(spGames):
            spg_policy = policy[i]
            valid_moves = self.game.get_valid_moves(states[i])
            spg_policy *= valid_moves
            spg_policy /= np.sum(spg_policy)
            
            # define root
            spg.root = Node(self.game, self.args, states[i], visit_count=1)
            spg.root.expand(spg_policy)
        
        # 1. selection
        for search in range(self.args['num_searches']):
            for spg in spGames:
                spg.node = None
                node = spg.root
                
                while node.is_fully_expanded():
                    node = node.select()
                    
                value, is_terminal = self.game.get_value_and_terminated(node.state, node.action_taken)  # if the result is that the player has won here then it is the antagonist and not the protagonist. What the sigma to that, i dont know how that is
                # if we want to read this value here from the node's/antagonist's perspective then we have to change it around
                value = self.game.get_opponent_value(value)
                
                if is_terminal:
                    # 4. backpropagation
                    node.backpropagate(value)
                else:
                    spg.node = node
            
            expandable_spGames = [mappingIdx for mappingIdx in range(len(spGames)) if spGames[mappingIdx].node is not None]
            if len(expandable_spGames)>0:
                states = np.stack([spGames[mappingIdx].node.state for mappingIdx in expandable_spGames])
                policy, value = self.model(
                    torch.tensor(self.game.get_encoded_state(states), device=self.model.device)
                )
                policy = torch.softmax(policy, axis=1).cpu().numpy()
                
            for i, mappingIdx in enumerate (expandable_spGames):
                node = spGames[mappingIdx].node
                spg_policy, spg_value = policy[i], value[i]
                valid_moves = self.game.get_valid_moves(node.state)
                spg_policy *= valid_moves  # all illegal moves will have a policy of 0
                spg_policy /= np.sum(spg_policy)
                
                node = node.expand(spg_policy)
                node.backpropagate(spg_value)
                
                
class SPG:  # SPG stands for self play game
    """
    Represents a single self-play game, containing its state, memory, and MCTS tree.

    This class encapsulates all the information needed for a self-play game, including
    the current game state, the memory of the game (for training data), and the
    Monte Carlo Tree Search (MCTS) tree used for move selection.

    ### Attributes:
            - state (np.array): The current state of the game board.
            - memory (list): A list of tuples, where each tuple contains:
                - The encoded game state (np.array).
                - The policy targets (action probabilities) (np.array).
                - The player's perspective (int).
            - root (Node): The root node of the MCTS tree for this game.
            - node (Node): The currently selected node in the MCTS tree.
    """
    def __init__(self, game):
        self.state = game.get_initial_state()
        self.memory = []
        self.root = None
        self.node = None
        
        
class AlphaZeroParallel:
    def __init__(self, model: ResNet, optimizer: torch.optim, game, args):
        self.model=model
        self.optimizer=optimizer
        self.game=game
        self.args=args
        self.mcts = MCTSParallel(game, args, model)
        
    def selfPlay(self):
        """
        Generates training data through parallel self-play games guided by MCTS.

        This function simulates multiple TicTacToe games concurrently, using the current
        neural network model to guide the Monte Carlo Tree Search (MCTS) for move selection.
        For each game, it performs one move per iteration, selects the best move based on
        MCTS visit counts, updates the game states, and stores the game history as training data.

        The training data consists of game states, policy targets (action probabilities),
        and game outcomes. This data is then used to train the neural network model to
        improve its policy and value predictions.

        ### Returns:
            - list: A list of tuples, where each tuple contains:
                - The encoded game state (np.array).
                - The policy targets (action probabilities) (np.array).
                - The game outcome (int).
        """
        
        return_memory = []
        player = 1
        spGames = [SPG(self.game) for spg in range(self.args['num_parallel_games'])]

        
        while len(spGames)>0:
            states = np.stack([spg.state for spg in spGames])
            
            neutral_states = self.game.change_perspective(states, player)
            self.mcts.search(neutral_states, spGames)
            
            for i in range(len(spGames))[::-1]:  # flipping range of self play games for perfect allignment
                spg = spGames[i]
                action_probs = np.zeros(self.game.action_size)
                for child in spg.root.children:
                    action_probs[child.action_taken] = child.visit_count
                action_probs /= np.sum(action_probs)
                
                spg.memory.append((spg.root.state, action_probs, player))
                
                temperature_action_probs = action_probs**(1/self.args['temperature'])  # adds randomness/noise, at temperature going to infinity the choice is almost random hence exploratory and at tempreature 1 the choice is exploitation
                action = np.random.choice(self.game.action_size, p=action_probs)
                
                spg.state = self.game.get_next_state(spg.state, action, player)
                
                value, is_terminal = self.game.get_value_and_terminated(spg.state, action)
                
                if is_terminal:
                    for hist_neutral_state, hist_action_probs, hist_player in spg.memory:
                        hist_outcome = value if hist_player == player else self.game.get_opponent_value(value)  # we want to recieve value if the player we started with has won (1 started and won) and otherwise -value if player we started with lsot (1 started and lost)
                        return_memory.append((
                            self.game.get_encoded_state(hist_neutral_state),
                            hist_action_probs,
                            hist_outcome
                        ))

                    del spGames[i]
                    
            player = self.game.get_opponent(player)
        
        return return_memory
    
    def train(self, memory):
        """
        Trains the neural network model using the provided training data.

        This function iterates through the training data in batches, calculates the policy and
        value losses, combines them, and updates the model's weights using gradient descent.

        ### Args:
                - memory (list): A list of tuples, where each tuple contains:
                    - The encoded game state (np.array).
                    - The policy targets (action probabilities) (np.array).
                    - The game outcome (int).

        ### Returns:
                - None. The function updates the model's weights in place.
    """
        
        shuffle(memory)
        for batchIdx in range(0, len(memory), self.args['batch_size']):
            sample = memory[batchIdx:batchIdx+self.args['batch_size']]
            state, policy_targets, value_targets = zip(*sample)
            
            state, policy_targets, value_targets = np.array(state), np.array(policy_targets), np.array(value_targets).reshape(-1, 1)
            
            state = torch.tensor(state, dtype=torch.float32, device=self.model.device)
            policy_targets = torch.tensor(policy_targets, dtype=torch.float32, device=self.model.device)
            value_targets = torch.tensor(value_targets, dtype=torch.float32, device=self.model.device)
            
            out_policy, out_value = self.model(state)
            
            policy_loss = F.cross_entropy(out_policy, policy_targets)
            value_loss = F.mse_loss(out_value, value_targets)
            loss = policy_loss+value_loss  
            # ⚠️⚠️⚠️ simply adding up loss can cause info loss. One: Bias due to one loss being bigger than the other as one is MSE and other is Cross entropy. Two: Adding rather than using them seperately
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
    
    def learn(self):
        """integrates the selfPlay and train function in a loop for num_iterations"""
        for iteration in range(self.args['num_iterations']):
            memory = []
            
            self.model.eval()
            for selfPlay_iteration in tqdm(range(self.args['num_selfPlay_iterations'] // self.args['num_parallel_games'])):
                memory += self.selfPlay()
                
            self.model.train()
            for epoch in tqdm(range(self.args['num_epochs'])):
                self.train(memory)
            
            torch.save(self.model.state_dict(), f"model_{iteration}.pt")
            torch.save(self.optimizer.state_dict(), f"optimizer_{iteration}.pt")