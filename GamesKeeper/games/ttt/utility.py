from math import floor

class Utility:
    @staticmethod
    def get_index(board_id, indice) -> int:
        return floor(board_id / 3**indice)%3

    @staticmethod
    def set_value(board_id, indice, new_value):
        old_value = Utility.get_index(board_id, indice)

        board_id -= old_value * 3**indice
        board_id += new_value * 3**indice

        return board_id

    @staticmethod
    def who_won(board_id):
        tmp = lambda x, y, z : Utility.get_index(board_id, x) == Utility.get_index(board_id, y) & Utility.get_index(board_id, y) == Utility.get_index(board_id, z) & Utility.get_index(board_id, z) != 0
        for i in range(3):
            if tmp(3*i, 3*i + 1, 3*i + 2):
                return Utility.get_index(board_id, 3*i)

        for i in range(3):
            if tmp(i, i+3, i+6):
                return Utility.get_index(board_id, i)

        if tmp(0, 4, 9):
            return Utility.get_index(board_id, 0)

        if tmp(2, 4, 6):
            return Utility.get_index(board_id, 2)

        return 0

    @staticmethod
    def get_board_list(board_id):
        return [Utility.get_index(board_id, i) for i in range(9)]

    @staticmethod
    def get_empty_indices(board_id):
        empty = []
        for i in range(9):
            if Utility.get_index(board_id, i) == 0:
                empty.append(i)
        return empty

    @staticmethod
    def set_board_list(board_list):
        return sum([value*3**i for i, value in enumerate(board_list)])

class BoardUtility:
    def __init__(self, board):
        self.board = board

    def get_index(self, indice) -> int:
        return Utility.get_index(self.board.id, indice)

    def set_value(self, indice, new_value):
        self.board.id = Utility.set_value(self.board.id, indice, new_value)

    def who_won(self):
        return Utility.who_won(self.board.id)

    def get_board_list(self):
        return Utility.get_board_list(self.board.id)

    def get_empty_indices(self):
        return Utility.get_empty_indices(self.board.id)

    def set_board_list(self, board_list):
        self.board.id = Utility.set_board_list(self.board.id)
