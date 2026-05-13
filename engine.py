class GameState():
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]
        
        self.moveFunctions = {'P':self.GetPawnMoves, 'R':self.GetRookMoves, 'N':self.GetNightMoves, 'B':self.GetBishopMoves, 'K':self.GetKingMoves, 'Q':self.GetQueenMoves}
        
        self.WhiteToMove = True
        self.MoveLog = []
        self.WhiteKingLocation = (7,4)
        self.BlackKingLocation = (0,4)
        self.inCheck = False
        self.pins = []
        self.checks = []
        
    # this will not work for castling and en-passant, pawn promotion
    def MakeMove(self, move: "Move"):
        self.board[move.StartRow][move.StartColumn] = "--"
        self.board[move.EndRow][move.EndColumn] = move.PieceMoved
        self.MoveLog.append(move)  # log the move so we can undo it later (?)
        self.WhiteToMove = not self.WhiteToMove  # swap players
        # update the kings location
        if move.PieceMoved == "wK":
            self.WhiteKingLocation = (move.EndRow, move.EndColumn)
        elif move.PieceMoved == "bK":
            self.BlackKingLocation = (move.EndRow, move.EndColumn)
            
    def UndoMove(self):
        if len(self.MoveLog)!=0:
            move:Move = self.MoveLog.pop()
            self.board[move.StartRow][move.StartColumn] = move.PieceMoved
            self.board[move.EndRow][move.EndColumn] = move.PieceCaptured
            self.WhiteToMove = not self.WhiteToMove
            if move.PieceMoved == "wK":
                self.WhiteKingLocation = (move.StartRow, move.StartColumn)
            elif move.PieceMoved == "bK":
                self.BlackKingLocation = (move.StartRow, move.StartColumn)
        
    # all moves considering checks
    def GetValidMoves(self):
        moves: list[Move] = []
        self.inCheck, self.pins, self.checks = self.checkForPinsAndChecks()
        if self.WhiteToMove:
            KingRow = self.WhiteKingLocation[0]
            KingCol = self.WhiteKingLocation[1]
        else:
            KingRow = self.BlackKingLocation[0]
            KingCol = self.BlackKingLocation[1]
        if self.inCheck:
            if len(self.checks) == 1:  # only 1 check, block check or move king
                moves = self.GetAllPossibleMoves()
                # to block a check you must move a piece into one of the squares between the enemy piece and king
                check = self.checks[0]  # check information
                check_row, check_col = check[0], check[1]
                PieceChecking = self.board[check_row][check_col]  # enemy piece causing the check
                ValidSquares = []  # squares that pices can move to
                # if night, must capture night or move king, other pieces can be blocked
                if PieceChecking[1] == "N":
                    ValidSquares = [(check_row, check_col)]
                else:
                    for i in range(1,8):
                        ValidSquare = (KingRow + check[2]*i, KingCol + check[3]*i)  # check 2 and 3 are check directions
                        ValidSquares.append(ValidSquare)
                        if ValidSquare[0] == check_row and ValidSquare[1] == check_col:  # once you get to piece end checks
                            break
                
                # get rid of any moves that dont block check or move king
                for i in range(len(moves), -1, -1, -1):  # go through a list backwards when removing element because that is better due to reasons explained
                    if moves[i].PieceMoved[1] != 'K':  # move doesnt move king so it must block or capture
                        if not (moves[i].EndRow, moves[i].EndColumn) in ValidSquares:  # move doesnt block check or capture piece
                            moves.remove(moves[i])
            
            else:  # double check, king has to move
                self.GetKingMoves(KingRow, KingCol, moves)
        
        else:  # not in check so all moves are fine
            moves = self.GetAllPossibleMoves()
            
        return moves
    
    def checkForPinsAndChecks(self):
        pins = []  # square where the ally pinned piece is and the direction it is pinned from
        checks = []  # square where the enemy is applying a check
        inCheck = False
        if self.WhiteToMove:
            EnemyColor = "b"
            AllyColor = "w"
            StartRow = self.WhiteKingLocation[0]
            StartCol = self.WhiteKingLocation[1]
        else:
            EnemyColor = "w"
            AllyColor = "b"
            StartRow = self.BlackKingLocation[0]
            StartCol = self.BlackKingLocation[1]
            
        # check outwards from king for pins and checks, keep track of pins
        directions = ((0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1))
        
        for j in range(len(directions)):
            d = directions[j]
            PossiblePin = ()  # reset the possible pins
            for i in range(1,8):
                EndRow = StartRow + d[0]*i
                EndCol = StartCol + d[1]*i
                if 0<=EndRow<8 and 0<=EndCol<8:
                    EndPiece = self.board[EndRow][EndCol]
                    if EndPiece[0] == AllyColor:   # ⚠️⚠️ what the sigma is the second condition for. something related to the phantom king beng protected by the real king at 38:00 of part 7
                        if PossiblePin==():  # first allied piece could be pinned
                            PossiblePin=(EndRow, EndCol, d[0], d[1])
                        else:  # 2nd allied piece, so no pin or check possible in this direction
                            break
                    
                elif EndPiece[0]==EnemyColor:
                    Type = EndPiece[1]
                    # 5 possiblitites in this complex condition:
                    # 1. orthogonally away from the king and the piece is a rook
                    # 2. diagonally away from the king and the piece is a bishop
                    # 3. 1 square away diagonally from the king and the piece is a pawn
                    # 4. any direction and the piece is a queen
                    # 5. any direction 1 square and the piece is a king
                    if (0 <= j <= 3 and Type == "R") or \
                        (4 <= j <= 7 and Type == "B") or \
                        (i == 1 and Type == "P" and ((EnemyColor == "w" and 6 <= j <= 7) or (EnemyColor == 'b' and 4 <= j <= 5))) or \
                        (Type == 'Q') or (i == 1 and Type == "K"):
                                if PossiblePin == ():  # no piece blocking, hence check
                                    inCheck=True
                                    checks.append((EndRow, EndCol, d[0], d[1]))
                                    break
                                else:  # piece blocking, so pin
                                    pins.append(PossiblePin)
                                    break
                                
                    else:  # enemy piece not applying pin
                        break
                else:
                    break  # off the board
        
        # check for Knight checks
        KnightMoves = ((-2,-1),(-2,1),(2,-1),(2,1),(1,2),(-1,2),(-1,-2),(1,-2))
        for m in KnightMoves:
            EndRow = StartRow + m[0]
            EndCol = StartCol + m[1]
            if 0<=EndCol<8 and 0<=EndRow<8:
                EndPiece = self.board[EndRow][EndCol]
                if EndPiece[0] == EnemyColor and EndPiece[1] == "N":  # enemy knight attacking king
                    inCheck = True
                    checks.append((EndRow, EndCol, m[0], m[1]))
        return inCheck, pins, checks
    
    # all moves not considering checks
    def GetAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn=='w' and self.WhiteToMove) or (turn=='b' and not self.WhiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r,c,moves)  # call the apt move piece function, instead of using 6 if statements
        return moves
                        
    def GetPawnMoves(self, r, c, moves):
        PiecePinned = False
        PinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                PiecePinned = True
                PinDirection = (self.pins[i][2], self.direction.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        if self.WhiteToMove:  # focus on white pawns
            if self.board[r-1][c] == "--":  # 1 square advance
                if not PiecePinned or PinDirection == (-1,0):  # if the pawn is moving in the direction it is pinned from then we have no problem, or otherwise if the piece is not pinned
                    moves.append(Move((r, c), (r-1, c), self.board))
                    if r == 6 and self.board[r-2][c] == "--":  # 2 square advance (happens only on the first move)
                        moves.append(Move((r,c),(r-2,c),self.board))
                    
            if c-1 >= 0:  # capture to the left
                if self.board[r-1][c-1][0] == 'b':  # enemy piece to capture
                    if not PiecePinned or PinDirection == (-1, -1):
                        moves.append(Move((r,c),(r-1,c-1),self.board))
            if c+1 <= 7:  # capture to right. we use a if and not an elif here because we want to be able to add both moves rather than just one to possible moves
                if self.board[r-1][c+1][0] == 'b':
                    if not PiecePinned or PinDirection == (-1, 1):  # ie if it is going in the direction of the pin
                        moves.append(Move((r,c), (r-1,c+1), self.board))
                        
        else:
            if self.board[r+1][c] == "--":
                if not PiecePinned or PinDirection==(1,0):
                    moves.append(Move((r,c),(r+1,c),self.board))
                    if r == 1 and self.board[r+2][c] == "--":
                        moves.append(Move((r,c),(r+2,c),self.board))
                
            if c-1 >= 0:
                if self.board[r+1][c-1][0] == 'w':
                    if not PiecePinned or PinDirection == (1,-1):
                        moves.append(Move((r,c),(r+1,c-1),self.board))
            if c+1 <= 7:
                if self.board[r+1][c+1][0] == 'w':
                    if not PiecePinned or PinDirection == (1,1):
                        moves.append(Move((r,c),(r+1,c+1),self.board))
        # add pawn promotions later
            
    def GetRookMoves(self, r, c, moves):
        PiecePinned = False
        PinDirection = ()
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                PiecePinned = True
                PinDirection = (self.pins[i][2], self.pins[i][3])
                if self.board[r][c][1] != 'Q':  # ⚠️⚠️ cant remove the queen on rook moves, only remove it on bishop move
                    self.pins.remove(self.pins[i])
                break
        
        directions = ((-1,0), (1,0), (0,-1), (0,1))
        EnemyColor = "b" if self.WhiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                EndRow = r + d[0]*i
                EndCol = c + d[1]*i
                if 0<=EndRow<8 and 0<=EndCol<8:
                    if not PiecePinned or PinDirection == d or PinDirection == (-d[0], -d[1]):  # the third or is to allow the rook to move not only in the direction of the pin but also in the direction away from the pin
                        EndPiece = self.board[EndRow][EndCol]
                        if EndPiece == "--":
                            moves.append(Move((r,c), (EndRow, EndCol), self.board))
                        elif EndPiece[0] == EnemyColor:
                            moves.append(Move((r,c), (EndRow, EndCol), self.board))
                            break
                        else:  # friendly color
                            break
                else:  # off board
                    break
    
    def GetBishopMoves(self, r, c, moves):
        directions = ((1,1), (1,-1), (-1,1), (-1,-1))
        EnemyColor = "b" if self.WhiteToMove else "w"
        PinDirection = ()
        PiecePinned = False
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                PiecePinned = True
                PinDirection = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
        
        for d in directions:
            for i in range(1,8):
                EndRow = r+d[0]*i
                EndCol = c+d[1]*i
                if 0<=EndRow<8 and 0<=EndCol<8:
                    if not PiecePinned or PinDirection==d or PinDirection==(-d[0],-d[1]):
                        EndPiece = self.board[EndRow][EndCol]
                        if EndPiece=="--":
                            moves.append(Move((r,c),(EndRow,EndCol),self.board))
                        elif EndPiece[0] == EnemyColor:
                            moves.append(Move((r,c), (EndRow, EndCol), self.board))
                            break
                        else:  # friendly color
                            break
                else:  # off board
                    break
    
    def GetNightMoves(self, r, c, moves):
        PiecePinned = False
        # pin direction doesnt matter for a knight
        for i in range(len(self.pins)-1, -1, -1):
            if self.pins[i][0] == r and self.pins[i][1] == c:
                PiecePinned = True
                self.pins.remove(self.pins[i])
                break
            
        KnightMoves = ((-2,-1),(-2,1),(2,-1),(2,1),(1,2),(-1,2),(-1,-2),(1,-2))
        AllyColor = "w" if self.WhiteToMove else "b"
        for m in KnightMoves:
            EndRow = r+m[0]
            EndColumn = c+m[1]
            if 0<=EndRow<8 and 0<=EndColumn<8:
                if not PiecePinned:
                    EndPiece = self.board[EndRow][EndColumn]
                    if EndPiece == "--" or EndPiece[0] != AllyColor:  # empty or enemy color
                        moves.append(Move((r,c),(EndRow,EndColumn),self.board))
    
    def GetKingMoves(self, r, c, moves):
        RowMoves = (-1, -1, -1, 0, 0, 1, 1, 1)
        ColMoves = (-1, 0, 1, -1, 1, -1, 0, 1)
        AllyColor = "w" if self.WhiteToMove else "b"
        for i in range(8):
            EndRow = r + RowMoves[i]
            EndCol = c + ColMoves[i]
            if 0 <= EndRow < 8 and 0<= EndCol <8:
                EndPiece = self.board[EndRow][EndCol]
                if EndPiece[0] != AllyColor:  # not an ally piece ie emptyt or enemy piece
                    # place king on end square and check for checks
                    if AllyColor == "w":
                        self.WhiteKingLocation = (EndRow, EndCol)
                    else:
                        self.BlackKingLocation = (EndRow, EndCol)
                    InCheck, pins, checks = self.checkForPinsAndChecks()
                    if not InCheck:
                        moves.append(Move((r,c),(EndRow,EndCol),self.board))
                    # place back king on orignal location
                    if AllyColor == 'w':
                        self.WhiteKingLocation = (r,c)
                    else:
                        self.BlackKingLocation = (r,c)
            
    
    def GetQueenMoves(self, r, c, moves):
        self.GetBishopMoves(r,c,moves)
        self.GetRookMoves(r,c,moves)

class Move():
    # maps keys to values ie key : value
    
    RankToRows = {"1":7, "2":6, "3":5, "4":4, "5":3, "6":2, "7":1, "8":0}
    RowsToRanks = {v:k for k, v in RankToRows.items()}
    FilesToCols = {"a":0, "b":1, "c":2, "d":3, "e":4, "f":5, "g":6, "h":7}
    ColsToFiles = {v:k for k, v in FilesToCols.items()}
    
    # overriding the equals to operator cause otherwise default python cant check for equality and we will never have a valid move 
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.MoveID == other.MoveID
        return False
    
    def __init__(self, StartSQ, EndSQ, board):
        self.StartRow = StartSQ[0]
        self.StartColumn = StartSQ[1]
        self.EndRow = EndSQ[0]
        self.EndColumn = EndSQ[1]
        self.PieceMoved = board[self.StartRow][self.StartColumn]
        self.PieceCaptured = board[self.EndRow][self.EndColumn]
        self.MoveID = self.StartRow * 1000 + self.StartColumn * 100 + self.EndRow * 10 + self.EndColumn
        
    def GetRankFile(self, r, c):
        return self.ColsToFiles[c] + self.RowsToRanks[r]
    
    def GetChessNotation(self):
        return self.GetRankFile(self.StartRow, self.StartColumn) + self.GetRankFile(self.EndRow, self.EndColumn)