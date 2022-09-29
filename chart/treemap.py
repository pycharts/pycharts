import matplotlib.cm
from matplotlib.figure import Figure
import random
from chart.chart import BaseChart
from utils.utils import get_root_node_key

class Treemap(BaseChart):
    def __init__(self, data):
        super().__init__(data)
        self.converted_data = self.__convert_data()
        self.figure = Figure((8, 6), 100)
        self.figure.gca().set_axis_off()
        self.__draw_treemap(self.converted_data)

    def get_figure(self):
        return self.figure

    def __convert_data(self):
        root_key = get_root_node_key(self.data) 
        keys = list(self.data.keys())
        keys.remove(root_key)

        converted_data = [root_key, None]
        converted_data[1] = self.__calculate_node_value(root_key, keys)
        return tuple(converted_data)

    def __calculate_node_value(self, node_key: str, key_list: list):
        if self.data[node_key][0] != None:
            return self.data[node_key][0]
        else:
            child_nodes = []
            for key in key_list:
                if self.data[key][1] == node_key:
                    new_key_list = list(key_list)
                    new_key_list.remove(key)
                    child_nodes.append((key, self.__calculate_node_value(key, new_key_list)))
            return tuple(child_nodes)
    
    def __calculate_tree(self, root):
        if type(root[1]) == int or type(root[1]) == float:
            return root
        elif type(root[1]) == tuple:
            value = 0
            child_nodes = root[1]
            subtrees = []
            for child_node in child_nodes:
                subtree = self.__calculate_tree(child_node)
                subtrees.append(subtree)
                # leaf node
                if len(subtree) == 2:
                    value += subtree[1]
                else:
                    value += subtree[2]
            subtrees.sort(key=lambda node : node[-1], reverse=True)
            return (
                root[0],
                tuple(subtrees),
                value
            )
        else:
            raise ValueError("Invalid node value")
    
    def __pad_rectangles(self, rects, pad=4):
        for rect in rects:
            rect["x"] += pad
            rect["dx"] -= 2*pad
            rect["y"] += pad
            rect["dy"] -= 2*pad
        return rects

    def __get_node_name(self, node):
        if type(node) != tuple:
            raise ValueError("Argument node is not a tuple")

        node_name = node[0]
        return node_name

    def __get_node_value(self, node):
        if type(node) != tuple:
            raise ValueError("Argument node is not a tuple")

        node_value = node[1]
        if type(node_value) == int or type(node_value) == float:
            return node_value
        elif type(node_value) == tuple:
            # calculated tree has the sum of all the children of a given node
            return node[2]
        else:
            raise ValueError("Invalid node value")
    
    def __normalize_sizes(self, named_sizes, dx, dy):
        """Normalize list of values.

        Normalizes a list of numeric values so that `sum(sizes) == dx * dy`.

        Parameters
        ----------
        named_sizes : list of tuples with (name, size)
            Input list of nodes to normalize.
        dx, dy : numeric
            The dimensions of the full rectangle to normalize total values to.

        Returns
        -------
        list[tupe(name, value)]
            The normalized values.
        """
        total_size = sum(node[1] for node in named_sizes)
        total_area = dx * dy
        named_sizes = map(lambda node: (node[0], float(node[1]) * total_area / total_size), named_sizes)
        return list(named_sizes)

    def __layoutrow(self, named_sizes, x, y, dx, dy):
        # generate rects for each size in sizes
        # dx >= dy
        # they will fill up height dy, and width will be determined by their area
        # sizes should be pre-normalized wrt dx * dy (i.e., they should be same units)
        covered_area = sum(node[1] for node in named_sizes)
        width = covered_area / dy
        rects = []
        for name, size in named_sizes:
            rects.append({"name": name, "x": x, "y": y, "dx": width, "dy": size / width})
            y += size / width
        return rects


    def __layoutcol(self, named_sizes, x, y, dx, dy):
        # generate rects for each size in sizes
        # dx < dy
        # they will fill up width dx, and height will be determined by their area
        # sizes should be pre-normalized wrt dx * dy (i.e., they should be same units)
        covered_area = sum(node[1] for node in named_sizes)
        height = covered_area / dx
        rects = []
        for name, size in named_sizes:
            rects.append({"name": name, "x": x, "y": y, "dx": size / height, "dy": height})
            x += size / height
        return rects


    def __layout(self, named_sizes, x, y, dx, dy):
        return (
            self.__layoutrow(named_sizes, x, y, dx, dy) if dx >= dy else self.__layoutcol(named_sizes, x, y, dx, dy)
        )

    def __worst_ratio(self, named_sizes, x, y, dx, dy): 
        return max(
            [
                max(rect["dx"] / rect["dy"], rect["dy"] / rect["dx"])
                for rect in self.__layout(named_sizes, x, y, dx, dy)
            ]
        )

    def __leftoverrow(self, named_sizes, x, y, dx, dy):
        # compute remaining area when dx >= dy
        covered_area = sum(node[1] for node in named_sizes)
        width = covered_area / dy
        leftover_x = x + width
        leftover_y = y
        leftover_dx = dx - width
        leftover_dy = dy
        return (leftover_x, leftover_y, leftover_dx, leftover_dy)


    def __leftovercol(self, named_sizes, x, y, dx, dy):
        # compute remaining area when dx >= dy
        covered_area = sum(node[1] for node in named_sizes)
        height = covered_area / dx
        leftover_x = x
        leftover_y = y + height
        leftover_dx = dx
        leftover_dy = dy - height
        return (leftover_x, leftover_y, leftover_dx, leftover_dy)


    def __leftover(self, named_sizes, x, y, dx, dy):
        return (
            self.__leftoverrow(named_sizes, x, y, dx, dy)
            if dx >= dy
            else self.__leftovercol(named_sizes, x, y, dx, dy)
        )

    def __squarify(self, named_sizes, x, y, dx, dy):
        """Compute treemap rectangles.

        Given a set of values, computes a treemap layout in the specified geometry
        using an algorithm based on Bruls, Huizing, van Wijk, "Squarified Treemaps".
        See README for example usage.

        Parameters
        ----------
        sizes : list-like of numeric values
            The set of values to compute a treemap for. `sizes` must be positive
            values sorted in descending order and they should be normalized to the
            total area (i.e., `dx * dy == sum(sizes)`)
        x, y : numeric
            The coordinates of the "origin".
        dx, dy : numeric
            The full width (`dx`) and height (`dy`) of the treemap.

        Returns
        -------
        list[dict]
            Each dict in the returned list represents a single rectangle in the
            treemap. The order corresponds to the input order.
        """
        named_sizes = list(map(lambda x: (x[0], float(x[1])), named_sizes))

        if len(named_sizes) == 0:
            return []

        if len(named_sizes) == 1:
            return self.__layout(named_sizes, x, y, dx, dy)

        # figure out where 'split' should be
        i = 1
        while i < len(named_sizes) and self.__worst_ratio(named_sizes[:i], x, y, dx, dy) >= self.__worst_ratio(
            named_sizes[: (i + 1)], x, y, dx, dy
        ):
            i += 1
        current = named_sizes[:i]
        remaining = named_sizes[i:]

        (leftover_x, leftover_y, leftover_dx, leftover_dy) = self.__leftover(current, x, y, dx, dy)
        return self.__layout(current, x, y, dx, dy) + self.__squarify(
            remaining, leftover_x, leftover_y, leftover_dx, leftover_dy
        )

    def __get_rectangles(self, node, x, y, dx=100, dy=100, pad=False):
        node_value = node[1]

        if type(node_value) != tuple:
            return []

        named_sizes = []
        for child in node_value:
            named_sizes.append(( self.__get_node_name(child), self.__get_node_value(child)))
        named_sizes = self.__normalize_sizes(named_sizes, dx, dy)
        named_sizes.sort(key=lambda x: x[1] , reverse=True)

        rectangles = self.__squarify(named_sizes, x, y, dx, dy)
        if pad:
            return self.__pad_rectangles(rectangles, dx, dy)
        return rectangles

    def __plot_rectangles(self, rectangles, colorable=False):
        ax = self.figure.gca()

        x = [rect["x"] for rect in rectangles]
        y = [rect["y"] for rect in rectangles]
        dx = [rect["dx"] for rect in rectangles]
        dy = [rect["dy"] for rect in rectangles]
        names = [rect["name"] for rect in rectangles]

        if colorable:
            color = (random.random(), random.random(), random.random())
            ax.bar(x, dy, width=dx, linewidth=1, edgecolor='black', bottom=y, color=color, align="edge")
        else:
            ax.bar(x, dy, width=dx, linewidth=1, bottom=y, color="white", align="edge")
        
        for i in range(len(rectangles)):
            ax.text(x[i] + 1, y[i] + dy[i] - 3, names[i])
        
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)

    def __draw_treemap(self, root):
        calculated_tree = self.__calculate_tree(root)

        # draw the rectangles of the first level of nodes
        level_rects = self.__get_rectangles(calculated_tree, 0, 0)
        self.__plot_rectangles(level_rects, True)
        # pad the drawn rectangles
        level_rects = self.__pad_rectangles(level_rects)

        if (type(calculated_tree[1]) == tuple and len(calculated_tree[1])):
            queue = []
            for i in range(len(calculated_tree[1])):
                queue.append((calculated_tree[1][i], level_rects[i]))

            while len(queue) > 0:
                node, rect = queue.pop(0)

                # Draw the inner rectangles of the node
                node_rects = self.__get_rectangles(node, rect["x"], rect["y"], rect["dx"], rect["dy"])
                self.__plot_rectangles(node_rects, True)
                node_rects = self.__pad_rectangles(node_rects)

                # Add children nodes to the queue
                if (type(node[1]) == tuple and len(node[1])):
                    for i in range(len(node[1])):
                        queue.append((node[1][i], node_rects[i]))





