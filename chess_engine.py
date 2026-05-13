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
        self.Checkmate = False
        self.Stalemate = False
        self.IsEnpassantMove = ()  # coordinates for the square where an enpasaant capture is possible
        self.CurrentCastlingRight =  CastleRights(True, True, True, True)
        self.CastleRightsLog = [CastleRights(self.CurrentCastlingRight.wks, self.CurrentCastlingRight.bks, 
                                             self.CurrentCastlingRight.wqs, self.CurrentCastlingRight.bqs)]
        
    # this will not work for castling and en-passant, pawn promotion
    def MakeMove(self, move: "Move"):
        self.board[move.StartRow][move.StartColumn] = "--"
        self.board[move.EndRow][move.EndColumn] = move.PieceMoved
        self.MoveLog.append(move)  # log the move
        self.WhiteToMove = not self.WhiteToMove  # swap players
        
        if move.PieceMoved == "wK":
            self.WhiteKingLocation = (move.EndRow, move.EndColumn)
        elif move.PieceMoved == "bK":
            self.BlackKingLocation = (move.EndRow, move.EndColumn)
        
        # Pawn promotion
        if move.IsPawnPromotion:
            self.board[move.EndRow][move.EndColumn] = move.PieceMoved[0] + 'Q'
        
        # En passant move: remove captured pawn
        if move.IsEnpassantMove:
            self.board[move.StartRow][move.EndColumn] = '--'  # Capture the pawn

        # Set en passant flag
        if move.PieceMoved[1] == 'P' and abs(move.StartRow - move.EndRow) == 2:
            self.IsEnpassantMove = ((move.StartRow + move.EndRow) // 2, move.StartColumn)
        else:
            self.IsEnpassantMove = ()
            
        # castle move
        if move.IsCastleMove:
            if move.EndColumn-move.StartColumn ==2:  # kingside castle
                self.board[move.EndRow][move.EndColumn-1] = self.board[move.EndRow][move.EndColumn+1]  # moves the rook
                self.board[move.EndRow][move.EndColumn+1] = '--'  # erase the old rook
            else:  # queen side cast
                self.board[move.EndRow][move.EndColumn+1] = self.board[move.EndRow][move.EndColumn-2]
                self.board[move.EndRow][move.EndColumn-2] = '--'
        
        # update castling rights - it is a rook or king move
        self.UpdateCastleRights(move)
        self.CastleRightsLog.append(CastleRights(self.CurrentCastlingRight.wks, self.CurrentCastlingRight.bks, 
                                             self.CurrentCastlingRight.wqs, self.CurrentCastlingRight.bqs))
        

    def UndoMove(self):
        if len(self.MoveLog) != 0:
            move: Move = self.MoveLog.pop()
            self.board[move.StartRow][move.StartColumn] = move.PieceMoved
            self.board[move.EndRow][move.EndColumn] = move.PieceCaptured
            self.WhiteToMove = not self.WhiteToMove

            if move.PieceMoved == "wK":
                self.WhiteKingLocation = (move.StartRow, move.StartColumn)
            elif move.PieceMoved == "bK":
                self.BlackKingLocation = (move.StartRow, move.StartColumn)

            # Undo en passant move
            if move.IsEnpassantMove:
                self.board[move.EndRow][move.EndColumn] = '--'  # Remove the capturing pawn
                direction = 1 if move.PieceMoved[0] == 'b' else -1
                self.board[move.EndRow - direction][move.EndColumn] = move.PieceCaptured  # Restore captured pawn
                self.IsEnpassantMove = (move.EndRow, move.EndColumn)

            # Undo two-square pawn advance
            if move.PieceMoved[1] == "P" and abs(move.StartRow - move.EndRow) == 2:
                self.IsEnpassantMove = ()
                
            # undo castling rights
            self.CastleRightsLog.pop()  # get rid of the new castle rights from the move we are undoing
            newRights = self.CastleRightsLog[-1]  # set the current castle rights to the last from list
            self.CurrentCastlingRight = CastleRights(newRights.wks, newRights.bks, newRights.wqs, newRights.bqs)  # might look silly but without this the undo doesnt work for some reason
            # undo the castle move
            if move.IsCastleMove:
                if move.EndColumn-move.StartColumn == 2:  # king side
                    self.board[move.EndRow][move.EndColumn+1] = self.board[move.EndRow][move.EndColumn-1]
                    self.board[move.EndRow][move.EndColumn-1] = '--'
                else:
                    self.board[move.EndRow][move.EndColumn-2] = self.board[move.EndRow][move.EndColumn+1]
                    self.board[move.EndRow][move.EndColumn+1] = '--'

    def UpdateCastleRights(self, move:"Move"):
        if move.PieceMoved == 'wK':
            self.CurrentCastlingRight.wks = False
            self.CurrentCastlingRight.wqs = False
        elif move.PieceMoved == 'bK':
            self.CurrentCastlingRight.bks = False
            self.CurrentCastlingRight.bqs = False
        elif move.PieceMoved == "wR":
            if move.StartRow == 7:
                if move.StartColumn == 0:  # left rook
                    self.CurrentCastlingRight.wqs = False
                elif move.StartColumn == 7:  # right rook
                    self.CurrentCastlingRight.wks = False
        elif move.PieceMoved == "bR":
            if move.StartRow == 0:
                if move.StartColumn == 0:  # left rook
                    self.CurrentCastlingRight.bqs = False
                elif move.StartColumn == 7:  # right rook
                    self.CurrentCastlingRight.bks = False
        
    # all moves considering checks
    def GetValidMoves(self):
        TempEnpassantPossible = self.IsEnpassantMove
        TempCastleRights = CastleRights(self.CurrentCastlingRight.wks, self.CurrentCastlingRight.bks, 
                                        self.CurrentCastlingRight.wqs, self.CurrentCastlingRight.bqs)
        # 1. Generate all possible moves
        moves = self.GetAllPossibleMoves()
        if self.WhiteToMove:
            self.GetCastleMoves(self.WhiteKingLocation[0], self.WhiteKingLocation[1], moves)
        else:
            self.GetCastleMoves(self.BlackKingLocation[0], self.BlackKingLocation[1], moves)
        # 2. for each move, make the move
        for i in range(len(moves)-1, -1, -1):  # when removing from a list go backwards through the list
            self.MakeMove(moves[i])
            # 3. generate all opponent moves
            # 4. for each of opponents move, see if they attack your king
            self.WhiteToMove = not self.WhiteToMove  # the make move switches the player from black to white and so this in check function will check for black king instead of white, so we need to switch the player back before we call it
            if self.inCheck():
                # 5. if they do attack your king, its not a valid move
                moves.remove(moves[i])
            self.WhiteToMove = not self.WhiteToMove  # switch back whilst keeping the move
            self.UndoMove()
        if len(moves)==0:  # either checkmate or stalemate
            if self.inCheck():
                self.Checkmate=True
            else:
                self.Stalemate=True
        else:
            self.Checkmate=self.Stalemate=False
        
        self.IsEnpassantMove = TempEnpassantPossible  # looks super innocent and useless but if we dont have this here then our enpassant value might not get reverted to how it was before the move when we do undo
        self.CurrentCastlingRight = TempCastleRights
        return moves
    
    def inCheck(self):
        if self.WhiteToMove:
            return self.SquareUnderAttack(self.WhiteKingLocation[0], self.WhiteKingLocation[1])
        else:
            return self.SquareUnderAttack(self.BlackKingLocation[0], self.BlackKingLocation[1])
        
    def SquareUnderAttack(self, r, c):
        self.WhiteToMove = not self.WhiteToMove  # switching the player
        OppMoves:list[Move] = self.GetAllPossibleMoves()
        self.WhiteToMove = not self.WhiteToMove  # switching the turns back to as it was because we dont want this function to modify the turn
        for move in OppMoves:
            if move.EndRow == r and move.EndColumn == c:  # square is under attack
                return True
        return False
                
                
    
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
        if self.WhiteToMove:  # focus on white pawns
            if self.board[r-1][c] == "--":  # 1 square advance
                moves.append(Move((r, c), (r-1, c), self.board))
                if r == 6 and self.board[r-2][c] == "--":  # 2 square advance (happens only on the first move)
                    moves.append(Move((r,c),(r-2,c),self.board))
                    
            if c-1 >= 0:  # capture to the left
                if self.board[r-1][c-1][0] == 'b':  # enemy piece to capture
                    moves.append(Move((r,c),(r-1,c-1),self.board))
                elif (r-1, c-1) == self.IsEnpassantMove:
                    moves.append(Move((r,c),(r-1,c-1),self.board, True))
            if c+1 <= 7:  # capture to right. we use a if and not an elif here because we want to be able to add both moves rather than just one to possible moves
                if self.board[r-1][c+1][0] == 'b':
                    moves.append(Move((r,c), (r-1,c+1), self.board))
                elif (r-1, c+1) == self.IsEnpassantMove:
                    moves.append(Move((r,c),(r-1,c+1),self.board, True))
                        
        else:
            if self.board[r+1][c] == "--":
                moves.append(Move((r,c),(r+1,c),self.board))
                if r == 1 and self.board[r+2][c] == "--":
                    moves.append(Move((r,c),(r+2,c),self.board))
                
            if c-1 >= 0:
                if self.board[r+1][c-1][0] == 'w':
                    moves.append(Move((r,c),(r+1,c-1),self.board))
                elif (r+1, c-1) == self.IsEnpassantMove:
                    moves.append(Move((r,c),(r+1,c-1),self.board, True))
            if c+1 <= 7:
                if self.board[r+1][c+1][0] == 'w':
                    moves.append(Move((r,c),(r+1,c+1),self.board))
                elif (r+1, c+1) == self.IsEnpassantMove:
                    moves.append(Move((r,c),(r+1,c+1),self.board, True))
            
    def GetRookMoves(self, r, c, moves):
        directions = ((-1,0), (1,0), (0,-1), (0,1))
        EnemyColor = "b" if self.WhiteToMove else "w"
        for d in directions:
            for i in range(1,8):
                EndRow = r + d[0]*i
                EndCol = c + d[1]*i
                if 0<=EndRow<8 and 0<=EndCol<8:
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
        for d in directions:
            for i in range(1,8):
                EndRow = r+d[0]*i
                EndCol = c+d[1]*i
                if 0<=EndRow<8 and 0<=EndCol<8:
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
        KnightMoves = ((-2,-1),(-2,1),(2,-1),(2,1),(1,2),(-1,2),(-1,-2),(1,-2))
        AllyColor = "w" if self.WhiteToMove else "b"
        for m in KnightMoves:
            EndRow = r+m[0]
            EndColumn = c+m[1]
            if 0<=EndRow<8 and 0<=EndColumn<8:
                EndPiece = self.board[EndRow][EndColumn]
                if EndPiece == "--" or EndPiece[0] != AllyColor:  # empty or enemy color
                    moves.append(Move((r,c),(EndRow,EndColumn),self.board))
    
    def GetKingMoves(self, r, c, moves):
        KingMoves = ((1,1),(1,0),(1,-1),(0,-1),(-1,-1),(-1,0),(-1,1),(0,1))  # Added (0,1) which was missing
        AllyColor = "w" if self.WhiteToMove else "b"
        for m in KingMoves:
            EndRow = r+m[0]
            EndColumn = c+m[1]
            if 0<=EndRow<8 and 0<=EndColumn<8:
                EndPiece = self.board[EndRow][EndColumn]
                if EndPiece == "--" or EndPiece[0] != AllyColor:  # empty or enemy color
                    moves.append(Move((r,c),(EndRow,EndColumn),self.board))
            
    
    def GetQueenMoves(self, r, c, moves):
        self.GetBishopMoves(r,c,moves)
        self.GetRookMoves(r,c,moves)
        
    def GetCastleMoves(self, r, c, moves):
        if self.SquareUnderAttack(r,c):
            return  # cant castle while we are in check
        if (self.WhiteToMove and self.CurrentCastlingRight.wks) or (not self.WhiteToMove and self.CurrentCastlingRight.bks):
            self.GetKingSideCastleMoves(r,c,moves)
        if (self.WhiteToMove and self.CurrentCastlingRight.wqs) or (not self.WhiteToMove and self.CurrentCastlingRight.bqs):
            self.GetQueenSideCastleMoves(r,c,moves)
        
    def GetKingSideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.SquareUnderAttack(r, c+1) and not self.SquareUnderAttack(r, c+2):
                moves.append(Move((r,c), (r,c+2), self.board, IsCastleMove=True))
    
    def GetQueenSideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--' and self.board[r][c-3] == '--':
            if not self.SquareUnderAttack(r, c-1) and not self.SquareUnderAttack(r,c-2):
                moves.append(Move((r,c), (r, c-2), self.board, IsCastleMove=True))
        
        
class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs
        


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
    
    def __init__(self, StartSQ, EndSQ, board, IsEnpassantPossible = False, IsCastleMove = False):
        self.StartRow = StartSQ[0]
        self.StartColumn = StartSQ[1]
        self.EndRow = EndSQ[0]
        self.EndColumn = EndSQ[1]
        self.PieceMoved = board[self.StartRow][self.StartColumn]
        self.PieceCaptured = board[self.EndRow][self.EndColumn]
        # pawn promotion
        self.IsPawnPromotion = (self.PieceMoved == 'wP' and self.EndRow == 0) or (self.PieceMoved == "bP" and self.EndRow == 7)
        # enpasant
        self.IsEnpassantMove = IsEnpassantPossible  # ⚠️ this might be a double equals to idk 
        if self.IsEnpassantMove:
            self.PieceCaptured = "wP" if self.PieceMoved == "bP" else "bP"
        self.MoveID = self.StartRow * 1000 + self.StartColumn * 100 + self.EndRow * 10 + self.EndColumn
        # castle move
        self.IsCastleMove = IsCastleMove
        
    def GetRankFile(self, r, c):
        return self.ColsToFiles[c] + self.RowsToRanks[r]
    
    def GetChessNotation(self):
        return self.GetRankFile(self.StartRow, self.StartColumn) + self.GetRankFile(self.EndRow, self.EndColumn)