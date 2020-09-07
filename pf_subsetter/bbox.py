
class BBox:

    def __init__(self, x_1=0, y_1=0, nx=0, ny=0, pad=(0, 0, 0, 0)):
        """
        _1 indexes are 1's based
        _0 are zero based
        human creates bbox using (1,1) as lower left
        bbox translates to 0's based needed for data processing
        padding order specified as (top, right, bottom, left)
        """
        self.pad_top = pad[0]
        self.pad_right = pad[1]
        self.pad_bottom = pad[2]
        self.pad_left = pad[3]
        self.x_1 = x_1
        self.y_1 = y_1
        self.nx = nx
        self.ny = ny
        self.x_0 = self.x_1 - 1
        self.y_0 = self.y_1 - 1

    def get_inner_extents(self):
        # return min_y, max_y, min_x, max_x without padding
        return self.y_0, self.y_0 + self.ny, self.x_0, self.x_0 + self.nx

    def get_padded_extents(self):
        x_0 = self.x_0 - self.pad_left
        x_end = x_0 + self.pad_left + self.pad_right + self.nx
        y_0 = self.y_0 - self.pad_bottom
        y_end = y_0 + self.pad_top + self.pad_bottom + self.ny
        return y_0, y_end, x_0, x_end

    def get_system_bbox(self):
        return self.x_0, self.y_0, self.nx, self.ny

    def get_human_bbox(self):
        return self.x_1, self.y_1, self.nx, self.ny
