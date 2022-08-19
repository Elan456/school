import egene
import pygame
import pygameTools as pgt

window_size = 800

gameDisplay = pygame.display.set_mode((window_size, window_size))
pygame.display.set_caption("Network Viewer")

# Set of inputs and outputs for training XOR
ins = [[0, 0], [0, 1], [1, 0], [1, 1]]
outs = [[0], [1], [1], [0]]

# Creating the species
guide = egene.Species([2, 2, 1], train_inputs=ins, train_outputs=outs, use_sigmoid=True, pop_size=100, add_bias_nodes=True,
                      native_window_size=window_size, noctcc=15)
for _ in range(1000):  # if you break up the training to one at a time you can see the network change over time.
    guide.train(1, print_population_losses=True)
    for event in pygame.event.get():
        pgt.basicinput(event, None)
    gameDisplay.blit(guide.get_best_network().draw(), (0, 0))
    pygame.display.update()

while True:
    testins = [float(a) for a in input(str(len(ins[0]))+" inputs separated by commas:\n").split(",")]
    print(guide.get_best_network().calico(testins, show_internals=False))
    img = guide.get_best_network().draw(show_internals=True, independent=True)
