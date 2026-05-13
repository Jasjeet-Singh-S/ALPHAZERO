import pygame as p
import chess_engine

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}
p.init()

def LoadImages():
    pieces = {"bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"}
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))

def DrawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color((60, 132, 166, 0.8))]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r+c) % 2]
            p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def HighlightSquare(screen, SQ_Selected, ValidMoves):
    if SQ_Selected != ():
        r, c = SQ_Selected
        # Highlight selected square
        s = p.Surface((SQ_SIZE, SQ_SIZE))
        s.set_alpha(100)  # Transparency value (0-255)
        s.fill(p.Color("yellow"))
        screen.blit(s, (c*SQ_SIZE, r*SQ_SIZE))
        
        # Highlight valid moves from that square
        s.fill(p.Color("green"))
        for move in ValidMoves:
            if move.StartRow == r and move.StartColumn == c:
                screen.blit(s, (move.EndColumn*SQ_SIZE, move.EndRow*SQ_SIZE))

def DrawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board.board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))

def DrawGameState(screen, gs, ValidMoves, SQ_Selected):
    DrawBoard(screen)  # Draw squares on the board
    HighlightSquare(screen, SQ_Selected, ValidMoves)  # Highlight square and possible moves
    DrawPieces(screen, gs)  # Draw pieces on top of those squares

def main():
    screen = p.display.set_mode((WIDTH, HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    gs = chess_engine.GameState()
    ValidMoves = gs.GetValidMoves()
    MoveMade = False
    
    LoadImages()
    running = True
    SQ_Selected = ()
    PlayerClicks = []
    
    while running:
        for e in p.event.get():
            if e.type == p.QUIT:
                running = False
            elif e.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                col = location[0]//SQ_SIZE
                row = location[1]//SQ_SIZE
                
                if SQ_Selected == (row, col):  # Clicked the same square twice
                    SQ_Selected = ()
                    PlayerClicks = []
                else:
                    SQ_Selected = (row, col)
                    PlayerClicks.append(SQ_Selected)
                
                if len(PlayerClicks) == 2:  # After second click
                    move = chess_engine.Move(PlayerClicks[0], PlayerClicks[1], gs.board)
                    print(move.GetChessNotation())
                    for i in range(len(ValidMoves)):
                        if move == ValidMoves[i]:
                            gs.MakeMove(ValidMoves[i])
                            MoveMade = True
                            SQ_Selected = ()
                            PlayerClicks = []
                    if not MoveMade:
                        PlayerClicks = [SQ_Selected]
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.UndoMove()
                    MoveMade = True
        
        if MoveMade:
           #AnimateMove(gs.MoveLog[-1], screen, gs, clock)
            ValidMoves = gs.GetValidMoves()
            MoveMade = False
            
        DrawGameState(screen, gs, ValidMoves, SQ_Selected)
        clock.tick(MAX_FPS)
        p.display.flip()

def AnimateMove(move:"chess_engine.Move", screen:p.display, board:chess_engine.GameState, clock:p.time.Clock):
    global colors
    dR = move.EndRow - move.StartRow
    dC = move.EndColumn - move.StartColumn
    FramesPerSquare = 10
    FrameCount = (abs(dR) + abs(dC)) * FramesPerSquare
    for frame in range(FrameCount+1):
        r,c = (move.StartRow+dR*frame/FrameCount, move.StartColumn+dC*frame/FrameCount)
        DrawBoard(screen)
        DrawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.EndRow + move.EndColumn) % 2]
        EndSquare = p.Rect(move.EndColumn*SQ_SIZE, move.EndRow*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, EndSquare)
        # draw the captures piece back onto rectangle
        if move.PieceCaptured != "--":
            screen.blit(IMAGES[move.PieceCaptured], EndSquare)
        # draw the moving piece
        screen.blit(IMAGES[move.PieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()