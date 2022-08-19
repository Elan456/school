import random
import math
import egene.pygameTools as pgt
import pkg_resources
from multiprocessing import Pool
import statistics as stat

import pygame
from pygame import gfxdraw
import os

# Libraries for colored console output
from colorama import Fore

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

icon = pkg_resources.resource_stream(__name__, 'images/Icon.png')

pygame.init()
pygame.display.set_caption("Network Viewer")
pygame.display.set_icon(pygame.image.load(icon))

black = (0, 0, 0)
white = (255, 255, 255)

colors = {"input": (37, 37, 125),
          "hidden": (100, 0, 0),
          "output": (0, 150, 0),
          "bias": (200, 0, 200)}


def sigmoid(x):
    """
    Uses the sigmoid function on x. High values become close to 1 while low/negative values become close to 0
    :return: The sigmoid of x, always between 0 and 1
    """
    try:
        y = 1 / (1 + math.e ** (-1 * x))
    except OverflowError:
        y = 0
    return y


def donata(x):
    """
    A function that does nothing. For nodes without an activation function
    :return: x
    """
    return x


def square(x):
    return x ** 2


class CustomError(Exception):
    pass


def duplicate_checker(x):
    """
    Checks if a list contains duplicates
    :param x: A list
    :return: True or False
    """
    unique_values = []

    for v in x:
        if v not in unique_values:
            unique_values.append(v)
        else:
            return True
    return False


def custom_eval(t):
    loss_function, network = t
    return loss_function(network)


class Species:
    def __init__(self, shape, train_inputs=None, train_outputs=None, initial_change_rate=1, pop_size=32, loss_function=None,
                 initial_weights=None, data_per_gen=None, use_sigmoid=True, can_change_change_rate=True, noctcc=4,
                 use_multiprocessing=True, set_all_zero=False, add_bias_nodes=True, native_window_size=500):
        self.use_multiprocessing = use_multiprocessing
        self.use_sigmoid = use_sigmoid
        self.can_change_change_rate = can_change_change_rate
        self.set_all_zero = set_all_zero
        self.add_bias_nodes = add_bias_nodes
        self.window_size = native_window_size
        self.no_changes_till_change_change_rate = noctcc

        self.epochs = 0  # Count of all epochs every trained on this species
        self.all_lowest_losses = []  # All the lowest losses for each epoch

        self.gens_since_change_change_rate = 0

        self.median_loss = None
        self.mean_loss = None

        if loss_function is None and train_inputs is None:
            raise CustomError("Species needs either a list of inputs and outputs or a loss_function")
        if loss_function is None:
            self.n_inputs = len(train_inputs[0])
            self.n_outputs = len(train_outputs[0])
            self.loss_function = self._evaluate
            self.using_custom_loss_function = False

        else:
            self.loss_function = loss_function
            self.using_custom_loss_function = True

        self.shape = shape  # This does not include the bias nodes which are added to every non-output layer

        if not self.using_custom_loss_function:
            if self.shape[0] != self.n_inputs:
                raise CustomError("First layer node count does not equal inputs number from training data which is:",
                                  self.n_inputs)
            if self.shape[-1] != self.n_outputs:
                raise CustomError("Last layer node count does not equal outputs number from training data which is:",
                                  self.n_outputs)
            if duplicate_checker(train_inputs):
                print("--Duplicate Inputs Found--")
            if data_per_gen is None:
                data_per_gen = len(train_inputs)
            self.data_per_gen = min(len(train_inputs), data_per_gen)
        else:
            self.data_per_gen = None

        self.initial_weights = initial_weights
        self.train_inputs = train_inputs
        self.train_outputs = train_outputs
        self.pop_size = pop_size
        self.change_rate = initial_change_rate

        self.networks = []

        for p in range(pop_size):  # Creating first generation of networks
            self.networks.append(Network(self.shape, self.use_sigmoid, self.add_bias_nodes, self.window_size, self.set_all_zero))
        # Giving the first network the initial weights
        if self.initial_weights is not None and self.set_all_zero is False:
            for v in range(len(self.networks[0].w)):
                self.networks[0].w[v].value = self.initial_weights[v]

    @staticmethod
    def _evaluate(p, inputs, output):  # Calculates the loss of a network based on a given input and output set
        loss = 0

        for active_input_index in range(len(inputs)):

            gen_output = p.calico(inputs[active_input_index])
            desired_output = output[active_input_index]
            for o in range(len(gen_output)):  # for handling networks with multiple outputs
                loss += abs(gen_output[o] - desired_output[o])

        loss /= len(inputs)  # division for average loss, to account for network with many outputs
        return loss

    def _assign_results_to_networks(self, results):
        if type(results[0]) is not tuple:  # No extra data given
            for a in range(len(self.networks)):
                self.networks[a].loss = results[a]
        elif len(results[0]) == 2:  # One extra return
            for a in range(len(self.networks)):
                self.networks[a].loss, self.networks[a].extra_data = results[a]
        else:
            CustomError("Too many values returned from loss function. Only one extra value is allowed as Network.extra_data")

    def _score_all(self, loss_function):  # Evaluates all the networks and puts them in order from best to worst

        if self.using_custom_loss_function:  # if a custom function is being use
            if self.use_multiprocessing:
                data = []
                p = Pool()
                for a in self.networks:
                    data.append((self.loss_function, a))
                results = p.map(custom_eval, data)

            else:
                results = []
                for a in range(len(self.networks)):
                    results.append(self.loss_function(self.networks[a]))

            self._assign_results_to_networks(results)
        else:  # If a list of inputs and outputs are being used for training
            inout = []  # List of tuples with each tuple having input, output
            for i in range(len(self.train_inputs)):
                inout.append((self.train_inputs[i], self.train_outputs[i]))
            random.shuffle(inout)
            ins = []
            outs = []
            for i in range(self.data_per_gen):
                ins.append(inout[i][0])
                outs.append(inout[i][1])
            for p in self.networks:
                p.loss = loss_function(p, ins, outs)

        self.networks.sort(key=lambda x: x.loss)  # Sorting them from best to worst

    def soft_restart(self):  # Resets all networks except the best one
        best = self.get_best_network()
        self.networks = []
        for p in range(self.pop_size):  # Creating first generation of networks
            self.networks.append(Network(self.shape, self.use_sigmoid, self.add_bias_nodes, self.window_size, self.set_all_zero))
        # Giving the first network the previous best weights
        self.networks[0] = best

    def _crossover(self, p1, p2):  # Crosses the weights of two parents to get a new child
        child = Network(self.shape, self.use_sigmoid, self.add_bias_nodes, self.window_size)
        num_weights = len(p1.w)
        cross_point = random.randint(0, num_weights - 1)
        orientation = random.choice([(p1, p2), (p2, p1)])  # Determines which parent is first

        for v in range(len(child.w)):  # Changes every weight
            if v < cross_point:
                child.w[v].value = orientation[0].w[v].value
            else:
                child.w[v].value = orientation[1].w[v].value

        return child

    def _mutate(self, network):  # Adds some random variation to some weights
        for w in network.w:
            w.value += random.random() * random.choice([-1, 0, 0, 0, 1]) * self.change_rate
        return network

    def _nextgen(self):  # Crosses over and mutates certain networks
        average_loss = sum([n.loss for n in self.networks]) / len(self.networks)
        stdv_loss = stat.pstdev([n.loss for n in self.networks])  # Population standard deviation of losses
        if stdv_loss == 0 and self.can_change_change_rate:
            print(Fore.YELLOW + "--\nThere is no variance amongst the population, raising change rate\n--")
            self.change_rate *= 8
            for n in range(len(self.networks) // 2, len(self.networks)):
                self.networks[n] = self._mutate(self.networks[n])
        elif stdv_loss == 0 and self.can_change_change_rate is False:
            print(Fore.YELLOW + "--\nThere is no variance amongst the population, but cannot raise change rate\n--")
        else:
            # Calculating z scores for a fairer comparisons
            # All networks with a negative z score (meaning they are better than the average) will be eligible as a parent
            # The chance of a network being a parent will be related to
            # what proportion their negative z score makes of all negative z scores.

            sum_of_negative_z_scores = 0
            for n in self.networks:
                # Calculating Z scores
                n.z_score = (n.loss - average_loss) / stdv_loss
                if n.z_score < 0:
                    sum_of_negative_z_scores += n.z_score

            # Getting what proportion each network with a negative z scores makes of the sum of the negative z scores
            parents = []
            for n in self.networks:
                if n.z_score < 0:
                    n.parent_chance = n.z_score / sum_of_negative_z_scores
                    parents.append(n)  # Adds the network to the list of parents
                else:  # All networks after the first network with a non-negative z score will be non-negative
                    break

            # Creating the new generation as a blank slate
            # This may be slow
            new_networks = []
            for p in range(self.pop_size):  # Creating first generation of networks
                new_networks.append(Network(self.shape, self.use_sigmoid, self.add_bias_nodes, self.window_size, self.set_all_zero))

            for p in range(len(new_networks)):  # Choosing the parents for each network from the previous networks
                p1, p2 = random.choices(parents, [p.parent_chance for p in parents], k=2)
                # It is possible for identical parents to occur

                new_networks[p] = self._crossover(p1, p2)  # Crosses the parents to produce a child
                new_networks[p] = self._mutate(new_networks[p])  # Mutates the child based on the change rate

            # Sets the weights of the old networks to that of the corresponding new network
            for i in range(1, len(self.networks)):  # The best network is left unchanged
                self.networks[i].set_weights(new_networks[i].show())

    def train(self, epochs, print_progress=True, print_population_losses=False):
        self.gens_since_change_change_rate += 1
        for v in range(epochs):

            self._score_all(self.loss_function)

            self.all_lowest_losses.append(self.networks[0].loss)
            if print_progress:
                print(Fore.BLUE + "\n" + str(self.epochs), Fore.RED + ":", "loss:", self.networks[0].loss, "| Weights:", self.networks[0].show())
            if self.can_change_change_rate:
                if len(self.all_lowest_losses) > self.no_changes_till_change_change_rate:
                    if self.gens_since_change_change_rate > self.no_changes_till_change_change_rate:  # We must be at least so many generations in
                        if self.all_lowest_losses[self.epochs - self.no_changes_till_change_change_rate] == self.all_lowest_losses[self.epochs]:  # No change
                            self.change_rate /= 2
                            if print_progress:
                                print(Fore.YELLOW + "--\nNo change from " + str(self.no_changes_till_change_change_rate) + " gens ago so change_rate is being lowered to", self.change_rate, "\n--")
                                self.gens_since_change_change_rate = 0

            if print_population_losses:
                all_losses = [a.loss for a in self.networks]
                self.mean_loss = sum(all_losses) / len(all_losses)
                self.median_loss = all_losses[len(all_losses) // 2]
                print(Fore.GREEN + "All Losses:  ", all_losses)
                print("Mean Loss:   ", self.mean_loss)
                print("Median Loss: ", self.median_loss)
            self.epochs += 1
            self._nextgen()

    def get_best_network(self):
        return self.networks[0]


class Network:
    # noinspection PyTypeChecker
    def __init__(self, shape, use_sigmoid, add_bias_nodes, window_size, set_all_zero=False):
        self.loss = 0
        self.use_sigmoid = use_sigmoid
        self.set_all_zero = set_all_zero
        self.shape = shape
        self.window_size = window_size
        self.parent_chance = 0

        self.extra_data = None  # Used for returning replay or any other data from the loss function

        # Initiate nodes ------------
        self.nodes = []
        x_scale = self.window_size / len(self.shape)
        x_start = x_scale / 2
        self.layer_starts = []  # Keeps track of where each layer starts so weights are created faster

        # Determining the radius of the nodes when drawn, so they all fit
        self.node_draw_size = min(int((self.window_size - 50) / max(self.shape) / 2.2), int(x_scale / 5))

        # Node Creation
        for active_layer in range(len(self.shape)):  # Each layer
            self.layer_starts.append(len(self.nodes))
            x = int(active_layer * x_scale + x_start)

            if add_bias_nodes and active_layer != len(self.shape) - 1:  # Prevents bias on output layer
                layer_size = self.shape[active_layer] + 1  # +1 for bias
            else:
                layer_size = self.shape[active_layer]
            for n in range(layer_size):  # Each node in the layer +1 for bias:
                if not (n == self.shape[active_layer] and active_layer == len(self.shape) - 1):  # Prevents bias on output layer
                    y_scale = (self.window_size - 50) / layer_size
                    y = int(n * y_scale + (y_scale / 2) + 25)
                    if active_layer == 0:
                        node_type = "input"
                    elif active_layer == len(self.shape) - 1:
                        node_type = "output"
                    else:
                        node_type = "hidden"

                    if n == self.shape[active_layer]:
                        node_type = "bias"  # Overrides other types
                    self.nodes.append(Network.Node(node_type, (x, y), active_layer, n, self.use_sigmoid, self.node_draw_size))

        self.layer_starts.append(len(self.nodes))
        things_checked = 0
        self.w = []
        for n in self.nodes:
            if n.layer != len(self.layer_starts) - 2:
                for target_index in range(self.layer_starts[n.layer + 1],
                                          self.layer_starts[n.layer + 2]):  # All nodes ahead in index are checked
                    things_checked += 1
                    t = self.nodes[target_index]

                    if t.layer == n.layer + 1:  # If the target node is one layer ahead of the current node
                        if t.node < self.shape[t.layer]:  # Stops weights from connecting to the bias node,
                            # weights can only connect from the bias node, not to bias node.

                            if self.set_all_zero is False:
                                self.w.append(Network.Edge(random.choice([-1, 1]) * random.random(), n, t))
                            else:
                                self.w.append(Network.Edge(0, n, t))
                        else:
                            pass
        self.w.sort(key=lambda x: x.pnode.layer)

        self.w_by_layer = [[] for _ in range(len(self.shape) - 1)]  # Organizing the weights by layer
        for v in self.w:
            self.w_by_layer[v.pnode.layer].append(v)  # These weights should still update by reference

    def set_weights(self, weights):
        for v in range(len(self.w)):
            self.w[v].value = weights[v]

    def _set_layer_values(self, layer, values):  # Sets the nodes of a layer to specific values. Used by calico
        for n in self.nodes:
            n.value = 0
        for n in self.nodes[self.layer_starts[layer]: self.layer_starts[layer + 1]]:
            if n.node == self.shape[layer]:  # Checks if the node is the bias node
                n.value = 1
            else:
                n.value = values[n.node]  # Sets the input nodes to their corresponding input

    def _feedforward_calculate(self):  # Starts at input layer and calculates forward
        for active_layer in range(len(self.shape) - 1):

            for n in self.nodes[self.layer_starts[active_layer]: self.layer_starts[active_layer + 1]]:
                n.value = n.activation_function(n.value)
                if n.type == "bias":
                    n.value = 1

            for v in self.w_by_layer[active_layer]:
                v.tnode.value += v.pnode.value * v.value

    def _collect_output_layer(self):  # Takes values of all output nodes and returns it as a list
        return [self.nodes[n].value for n in range(len(self.nodes) - self.shape[-1], len(self.nodes))]

    def list_internal_values(self):  # Prints the value of every node and edge
        for n in self.nodes:
            print("Layer: ", n.layer, "| Node: ", n.node, "| Value: ", n.value)
        for we in self.w:
            print("PNode:", (we.pnode.layer, we.pnode.node), "| TNode:", (we.tnode.layer, we.tnode.node),
                  "| Value:", we.value)

    def calico(self, inputs, show_internals=False):  # Using an input and its weights the network returns an output
        if type(inputs) is not list:
            raise CustomError("Calico input is not a list")

        self._set_layer_values(0, inputs)  # Sets the input layer to the input values

        self._feedforward_calculate()

        if show_internals:
            self.list_internal_values()

        return self._collect_output_layer()

    def calico_from_hidden_layer(self, layer, values, show_internals=False):  # Starts the feedforward at a different layer
        self._set_layer_values(layer, values)  # Sets the selected layer to the given values

        for active_layer in range(len(self.shape) + 1):  # Only feed forwards from the starting layer
            if active_layer >= layer:
                for n in self.nodes:
                    if n.layer == active_layer:
                        n.value = n.activation_function(n.value)
                for v in self.w:
                    if v.pnode.layer == active_layer:
                        v.tnode.value += v.pnode.value * v.value

        if show_internals:
            self.list_internal_values()
        return self._collect_output_layer()

    class Node:
        def __init__(self, node_type, location, layer, node, use_sigmoid, draw_size):
            self.type = node_type
            self.color = colors[self.type]
            self.location = location
            self.layer = layer
            self.node = node
            self.value = 0
            self.draw_size = draw_size

            if self.type == "hidden":
                if not use_sigmoid:

                    self.activation_function = donata
                    self.color = (255, 128, 0)
                else:

                    self.activation_function = sigmoid
                    self.color = (12, 122, 67)
            else:
                self.activation_function = donata

        def draw(self, display):

            gfxdraw.aacircle(display, self.location[0], self.location[1], self.draw_size + 1, white)
            gfxdraw.filled_circle(display, self.location[0], self.location[1], self.draw_size + 1, white)
            gfxdraw.aacircle(display, self.location[0], self.location[1], self.draw_size, self.color)
            gfxdraw.filled_circle(display, self.location[0], self.location[1], self.draw_size, self.color)
            if self.type == "bias":
                pygame.draw.rect(display, white,
                                 [self.location[0] - self.draw_size - 1, self.location[1] - self.draw_size - 1,
                                  self.draw_size, self.draw_size * 2 + 3])
                pygame.draw.rect(display, self.color,
                                 [self.location[0] - self.draw_size, self.location[1] - self.draw_size, self.draw_size,
                                  self.draw_size * 2 + 1])

    class Edge:  # The connection between nodes with weights
        def __init__(self, value, pnode, tnode):  # Each weight has a value and connects the pnode to the tnode
            self.value = value
            self.pnode = pnode
            self.tnode = tnode  # The tnode must be one layer ahead of the pnode

        def draw(self, width, display, node_radius):
            if width > 0:
                if self.value > 0:
                    c = (0, 100, 0)
                elif self.value < 0:
                    c = (100, 0, 0)
                else:
                    c = (255, 255, 255)
                start_loc = (self.pnode.location[0] + node_radius - width, self.pnode.location[1])
                end_loc = (self.tnode.location[0] - node_radius + width, self.tnode.location[1])
                # yf.draw_line_as_polygon(display, (self.pnode.location[0] + node_radius, self.pnode.location[1]), (self.tnode.location[0] - node_radius, self.tnode.location[1]), width, (100, 100, 100))
                pgt.draw_line_as_polygon(display, start_loc, end_loc, width, c)
            # pygame.draw.line(display, black, self.pnode.location, self.tnode.location, width + 2)
            # pygame.draw.line(display, c, self.pnode.location, self.tnode.location, width)

    def show(self):  # A list of all weights
        a = []
        for v in self.w:
            a.append(v.value)
        return a

    def draw(self, independent=False, show_internals=True):
        display = None  # If independent, this becomes a pygame window
        if independent:
            # Reinitializing the font
            pygame.font.init()
            display = pygame.display.set_mode((self.window_size, self.window_size))

        surface = pygame.Surface((self.window_size, self.window_size))
        largest_weight = max([abs(v.value) for v in self.w])

        for p in self.w:
            p.draw(round((abs(p.value) / largest_weight) * self.node_draw_size * .3, 0), surface, self.node_draw_size)
        if show_internals:
            for p in self.w:  # Again so the text is not covered by any edges
                pgt.text(surface, ((p.tnode.location[0] + p.pnode.location[0] * 1.5) / 2.5,
                                   (p.tnode.location[1] + p.pnode.location[1] * 1.5) / 2.5), str(round(p.value, 2)), white, 20)
        for n in self.nodes:
            n.draw(surface)
            if show_internals:
                pgt.text(surface, n.location, str(round(n.value, 2)), white, 20)

        while independent:
            display.blit(surface, (0, 0))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    independent = False
                    pygame.quit()

        return surface
