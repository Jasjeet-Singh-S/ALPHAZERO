import numpy as np
import math

class TicTacToe:
    def __init__(self):
        """
            initalizes the TicTacToe class
        """
        self.row_count = 3
        self.column_count = 3
        self.action_size = self.row_count * self.column_count
        
    def get_initial_state(self):
        """
            creates a numpy matrix of row*column 0's which represent untouched cells on the board
            
            ### Parameters: 
                    - None
                    
            ### Returns: 
                    - numpy array
        """
        return np.zeros((self.row_count, self.column_count))
    
    def get_next_state(self, state, action, player):
        """
            extracts the position of the players marker on the board (row, column) from action and saves it in state
    
            ### Parameters: 
                    - state (int[3][3]): a matrix of 3x3 that represents the state of the game with the posistion of each piece of both players
                    - action (int): an integer that represents the position of the player marker as {row*3 + column}
                    - player (int): a unique integer flag representing a player and their piece on the board
                    
            ### Returns: 
                    - state (int[3][3])
        """
        row = action // self.column_count       # 8 will mean row 3, 4 will mean row 2 etc etc
        column = action % self.column_count     # 3 will mean oclumn 1, 4 will mean column 2 etc etc
        state[row,column] = player              # places the piece of the player on the board
        return state
    
    def get_valid_moves(self,state):
        """
            returns all played and unplayed cell in the matrix/board 
    
            ### Parameters: 
                    - state (int[3][3]): a matrix of 3x3 that represents the state of the game with the posistion of each piece of both players
                    
            ### Returns: 
                    - 1D boolean array of lenght 9 converted to integer representing occupied and unoccupied positions on the board, where 0 is invalid (occupied) cell and 1 is valid (occupied) cell.
        """
        return (state.reshape(-1) == 0).astype(np.uint8)
    
    def check_win(self, state, action):
        """
            Checks if a player has won or not. Sums the pieces in horizontal and diagonal lines to see if they are equal to 3 (or -3).
    
            ### Parameters: 
                    - state (int[3][3]): a matrix of 3x3 that represents the state of the game with the posistion of each piece of both players
                    - action (int): an integer that represents the position of the player marker as {row*3 + column}
                    
            ### Returns: 
                    - a boolean (T/F)
        """
        if action == None:  # special case for the root node because it is initialised with action set to None and we dont want out code erroring cause of that
            return False
        
        row = action // self.column_count
        column = action % self.column_count
        player = state[row, column]
        
        return (
            np.sum(state[row, :]) == player * self.column_count                     # checks all rows for a straight line of pieces
            or np.sum(state[:, column]) == player * self.row_count                  # checks all columns for a strain line of pieces
            or np.sum(np.diag(state)) == player * self.row_count                    # checks left to right diagonal for a straight line of pieces
            or np.sum(np.diag(np.flip(state, axis=0))) == player * self.row_count   # checss right to left diagonal for a straight line of pieces
        )
    
    def get_value_and_terminated(self, state, action):
        """
            returns (int, bool) 1 if player has won and 0 otherwise, and True if game terminated and False otherwise 
        """
        if self.check_win(state, action):
            return 1, True
        if np.sum(self.get_valid_moves(state)) == 0:
            return 0, True
        return 0, False
    
    def get_opponent(self, player):
        """for switching between the two players"""
        return -player
    
    def get_opponent_value(self, value):
        """uses player 1 score to evaluate player 2 score by simply returning the negative of player 1 score as TicTacToe is a zero sum game"""
        return -value
    
    def change_perspective(self, state, player):
        return state*player
    

class Node:
    def __init__(self, game:TicTacToe, args, state, parent=None, action_taken=None):
        """initializes the Node class"""
        self.game = game 
        self.args = args
        self.state = state
        self.parent = parent
        self.action_taken = action_taken
        
        self.children = []
        self.expandable_moves = game.get_valid_moves(state)
        
        self.visit_count = 0
        self.value_sum = 0
        
    def is_fully_expanded(self):
        """checks if all states possible from a node (except that leaf/terminal node) have been visited or not"""
        return np.sum(self.expandable_moves) == 0 and len(self.children) > 0
    
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
        q_value = 1 - ((child.value_sum/child.visit_count) + 1) / 2  # what teh sigma. author says its possible to have negative value sum from -1 to 1 so we add one and divide by 2 so this turns into a probability and we subtract it all from 1 because child is of antagonist whereas parent which actually usues the UCB is of the protagonist
        return q_value + self.args['C'] * math.sqrt(math.log(self.visit_count/child.visit_count))
    
    def expand(self):
        """creates a new node for a valid move in expandable_moves()"""
        action = np.random.choice(np.where(self.expandable_moves==1)[0])  # the [0] extracts the index we need from the result of np.where
        self.expandable_moves[action] = 0
        
        child_state = self.state.copy()
        child_state = self.game.get_next_state(child_state, action, 1)
        child_state = self.game.change_perspective(child_state, player=-1)
        
        child = Node(self.game, self.args, child_state, self, action)
        self.children.append(child)
        return child
        
    def simulate(self):
        """
            performs a random rollout from the current node's state to estimate the value of the state. 
        """
        
        # this is like minecraft where when we are in a mine and the mine splits into two paths and we havent seen either, this is like just setting torches in any of the two paths randomly just for expanding our knoweldge of the area, we're basically just lighting up a previously unexplored dark area
        
        value, is_terminal = self.game.get_value_and_terminated(self.state, self.action_taken)  # check if game is terminated or not and if won or not 
        value = self.game.get_opponent_value(value)  # change the value of won or not to opponents perspective
        
        if is_terminal:
            return value
        
        rollout_state = self.state.copy()
        rollout_player = 1
        while True:
            valid_moves = self.game.get_valid_moves(rollout_state)
            action = np.random.choice(np.where(valid_moves == 1)[0])
            rollout_state = self.game.get_next_state(rollout_state, action, rollout_player)
            value, is_terminal = self.game.get_value_and_terminated(rollout_state, action)
            if is_terminal:
                if rollout_player==-1:
                    value = self.game.get_opponent_value(value)
                return value
            
            rollout_player = self.game.get_opponent(rollout_player)
            
    def backpropagate(self, value):
        self.value_sum += value
        self.visit_count += 1
        
        value = self.game.get_opponent_value(value)
        if self.parent is not None :
            self.parent.backpropagate(value)
            
            
class MCTS:
    def __init__(self, game:TicTacToe, args):
        self.game = game
        self.args = args
        
    def search(self, state):
        
        # define root
        root = Node(self.game, self.args, state)
        
        # 1. selection
        for search in range(self.args['num_searches']):
            node = root
            
            while node.is_fully_expanded():
                node = node.select()
                
            value, is_terminal = self.game.get_value_and_terminated(node.state, node.action_taken)  # if the result is that the player has won here then it is the antagonist and not the protagonist. What the sigma to that, i dont know how that is
            # if we want to read this value here from the node's/antagonist's perspective then we have to change it around
            value = self.game.get_opponent_value(value)
            
            if not is_terminal:
                # 2. expansion
                node = node.expand()
                
                # 3. simulation
                value = node.simulate()
            
            # 4. backpropagation
            node.backpropagate(value)
            
        # return visit counts
        action_probs = np.zeros(self.game.action_size)
        for child in root.children:
            action_probs[child.action_taken] = child.visit_count
        action_probs /= np.sum(action_probs)
        return action_probs
    
    
tictactoe = TicTacToe()
player = 1

args = {
    'C' : 1.41,  # sqrt(2) 
    'num_searches' : 1000
}

mcts = MCTS(tictactoe, args)
state = tictactoe.get_initial_state()

while True:
    print(state)
    
    if player ==1:
        valid_moves = tictactoe.get_valid_moves(state)
        print(f"valid_moves : {[i for i in range(tictactoe.action_size) if valid_moves[i]==1]}")
        action = int(input(f"{player}: "))
        
        if valid_moves[action] == 0:
            print("action not valid")
            continue
    
    else:
        neutral_state = tictactoe.change_perspective(state, player)
        mcts_probs = mcts.search(neutral_state)
        action = np.argmax(mcts_probs)
    
    state = tictactoe.get_next_state(state, action, player)
    
    value, is_terminal = tictactoe.get_value_and_terminated(state, action)
    
    if is_terminal:
        print(state)
        if value == 1:
            print(f"{player} won")
        else:
            print("draw")
        break
    
    player = tictactoe.get_opponent(player)