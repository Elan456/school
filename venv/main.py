import pygame
import yseful
import math as m
import random as r
import pathing
import quadtree
import pickle
from img_to_map import *
from teacher import Teacher

blindteacher = True
deafteacher = False
constantchase = False

aidebug = True
pygame.init()

pygame.mixer.music.load('Floor.wav')

clap_sound = pygame.mixer.Sound('clap.wav')
ding_sound = pygame.mixer.Sound('ding.wav')
ihear_sound = pygame.mixer.Sound('iheardthat.wav')
morekeys_sound = pygame.mixer.Sound('morekeys.wav')
onemore_sound = pygame.mixer.Sound('onemore.wav')
outofhere_sound = pygame.mixer.Sound('outofhere.wav')
detention_sound = pygame.mixer.Sound('detention.wav')
comingfor_sound = pygame.mixer.Sound('comingfor.wav')
deliver_sound = pygame.mixer.Sound('deliver.wav')
iwant_sound = pygame.mixer.Sound('iwant.wav')
thankyou_sound = pygame.mixer.Sound('thankyou.wav')
yes_sound = pygame.mixer.Sound('yes.wav')
ifihad_sound = pygame.mixer.Sound('ifihad.wav')

pathing_map = pickle.load(open("SchoolPathing.p", "rb"))
print("nodes count for pathing:", len(pathing_map.nodes))
sight_map = pickle.load(open("SchoolSight.p", "rb"))  # Ignores furniture but has doors blocking
print("map loaded")

clock = pygame.time.Clock()

dissize = 1000

gameDisplay = pygame.display.set_mode((dissize, dissize))

aiSurface = pygame.Surface((1920, 3200))

school = pygame.image.load('school.png')
schoolsee = pygame.image.load('school.png')

aiSurface.blit(school, (0, 0))

white = (255, 255, 255)
yellow = (255, 255, 0)
blue = (0, 0, 200)
green = (0, 150, 0)
red = (255, 0, 0)
black = (0, 0, 0)
dark_red = (200, 0, 0)
bright_green = (0, 255, 0)
purple = (255, 0, 255)
CameraX = 1040 - dissize / 2
CameraY = 2480 - dissize / 2
grey = (50, 50, 50)
orange = (255, 128, 0)
vendingx = 1036
vendingy = 1843
brown = (128, 64, 0)

hasmessage = 0

# TEACHERSTUFF
teacherwalkspeed = 2  # 2
teacherrunspeed = 4.1  # 4.1
teacheraccl = .1  # .1
keynum = 6
boispeed = 1
hearwalk = 100
doorhear = 5000

# MOLE
molespeed = .5



def text_objects(text, font):
    textSurface = font.render(text, True, black)
    return textSurface, textSurface.get_rect()


def text_e(text, font):
    textSurface = font.render(text, True, w_red)
    return textSurface, textSurface.get_rect()


def button(msg, x, y, w, h, ic, ac, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(gameDisplay, ac, (x, y, w, h))
        if click[0] == 1 and action != None:
            if action == "play":
                game()
            elif action == "quit":
                pygame.quit()
                quit()
            action()
    else:
        pygame.draw.rect(gameDisplay, ic, (x, y, w, h))

    smallText = pygame.font.Font('freesansbold.ttf', 20)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ((x + (w / 2)), (y + (h / 2)))
    gameDisplay.blit(textSurf, textRect)


def dschool():
    gameDisplay.blit(schoolsee, (0 - CameraX, 0 - CameraY))


def boi(x, y):
    pygame.draw.circle(gameDisplay, yellow, (x - CameraX, y - CameraY), 10)
    pygame.draw.circle(gameDisplay, blue, (x - CameraX, y - CameraY), 10, width=2)


def otherstudent(x, y):
    pygame.draw.circle(gameDisplay, (200, 200, 0), (x - CameraX, y - CameraY), 10)
    pygame.draw.circle(gameDisplay, blue, (x - CameraX, y - CameraY), 10, width=2)


def draw_teacher(x, y, drawteacher, direction, boix, boiy):
    pygame.draw.circle(gameDisplay, (0, 3 * (50 - drawteacher) + 100, 0), (x - CameraX, y - CameraY), 20)
    pygame.draw.circle(gameDisplay, blue, (x - CameraX, y - CameraY), 20, width=2)

    # EYES
    eyeball1 = (7 * m.cos(direction + 1) + x - CameraX, 7 * m.sin(direction + 1) + y - CameraY)
    eyeball2 = (7 * m.cos(direction - 1) + x - CameraX, 7 * m.sin(direction - 1) + y - CameraY)

    pygame.draw.circle(gameDisplay, white, eyeball1, 5)
    pygame.draw.circle(gameDisplay, white, eyeball2, 5)

    pupil1Direction = m.atan2(boiy - (eyeball1[1] + CameraY), boix - (eyeball1[0] + CameraX))
    # pupil1Direction = direction + m.pi/2
    pupil1 = (2 * m.cos(pupil1Direction) + eyeball1[0], 2 * m.sin(pupil1Direction) + eyeball1[1])

    pupil2Direction = m.atan2(boiy - (eyeball2[1] + CameraY), boix - (eyeball2[0] + CameraX)) + m.pi
    # pupil2Direction = direction - m.pi/2
    pupil2 = (2 * m.cos(pupil2Direction) + eyeball2[0], 2 * m.sin(pupil2Direction) + eyeball2[1])

    pygame.draw.circle(gameDisplay, red, pupil1, 2)
    pygame.draw.circle(gameDisplay, red, pupil2, 2)


def mole(x, y):
    pygame.draw.circle(gameDisplay, brown, (int(x - CameraX), int(y - CameraY)), 5)


def closest(tx, ty, path):
    lowest = 10000
    for v in range(len(path)):
        d = yseful.cdistance(tx, ty, path[v][0], path[v][1])
        if d < lowest:
            lowest = d
            best = v
    return (path[best])


def keys(locs):
    for v in range(len(locs)):
        pygame.draw.circle(gameDisplay, red, (locs[v][0] - CameraX, locs[v][1] - CameraY), 5)


def shroud(maxx, maxy, minx, miny):
    pygame.draw.rect(gameDisplay, grey, [0, 0, dissize, miny])
    pygame.draw.rect(gameDisplay, grey, [0, maxy, dissize, dissize])

    pygame.draw.rect(gameDisplay, grey, [0, 0, minx, dissize])
    pygame.draw.rect(gameDisplay, grey, [maxx, 0, dissize, dissize])


def menu():
    intro = True

    while intro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(white)
        largeText = pygame.font.Font('freesansbold.ttf', 115)
        TextSurf, TextRect = text_objects('School', largeText)
        TextRect.center = ((dissize / 2), (dissize / 5))
        gameDisplay.blit(TextSurf, TextRect)

        button("START", 300, 450, 100, 50, green, bright_green, action=normal)
        button("QUIT", dissize - 400, 450, 100, 50, dark_red, red, 'quit')
        button("EXTREME MODE", dissize / 2 - 87.5, 550, 175, 50, purple, red, extreme)
        button("INSANE MODE", dissize / 2 - 87.5, 900, 175, 50, purple, red, superextreme)
        button("INFO", 0, 500, 100, 50, white, white, action=None)
        button("Deliver messages between students for $1 per message.", 250, 600, 100, 50, white, white, action=None)
        button("Use the money to buy an energy drink in the cafe.", 200, 700, 100, 50, white, white, action=None)
        button("The drink increases your running speed", 200, 800, 100, 50, white, white, action=None)

        pygame.display.update()
        clock.tick(15)


def extreme():
    global teacheraccl
    global keynum
    global molespeed
    teacheraccl = 1
    keynum = 20
    molespeed = 2
    game()


def superextreme():
    global teacheraccl
    global keynum
    global boispeed
    global teacherwalkspeed
    global molespeed
    molespeed = 1.5
    teacherwalkspeed = 4

    boispeed = .5

    teacheraccl = 1
    keynum = 20
    game()


def normal():
    global teacheraccl
    global keynum
    global boispeed
    global teacherwalkspeed
    global molespeed
    global hasmessage
    hasmessage = 0

    # TEACHERSTUFF
    teacherwalkspeed = 2  # 2
    teacherrunspeed = 4.1  # 4.1
    teacheraccl = .1  # .1
    keynum = 6
    boispeed = 1
    # MOLE
    molespeed = .5
    game()


def victory():
    endtro = True

    while endtro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(green)
        largeText = pygame.font.Font('freesansbold.ttf', 115)
        TextSurf, TextRect = text_objects('YOU WIN!', largeText)
        TextRect.center = ((dissize / 2), (dissize / 5))
        gameDisplay.blit(TextSurf, TextRect)

        pygame.display.update()
        clock.tick(15)


def maxandmin(light):
    MAXx = 0
    MAXy = 0
    MINx = 100000
    MINy = 100000

    for v in light:
        if v[0] > MAXx:
            MAXx = v[0]
        if v[0] < MINx:
            MINx = v[0]
        if v[1] > MAXy:
            MAXy = v[1]
        if v[1] < MINy:
            MINy = v[1]

    return ([MAXx, MAXy, MINx, MINy])


def movepackage(locals, keys):
    start = (0, 0)
    end = (0, 0)
    while start == end or start in keys or end in keys:
        start = r.choice(locals)
        end = r.choice(locals)

    return (start, end)


def acceptsmessage():
    global hasmessage
    hasmessage = True


def arrow(ux, uy, tx, ty):
    direction = m.atan2(ty - uy, tx - ux)
    magnitude = 50
    x = magnitude * m.cos(direction)
    y = magnitude * m.sin(direction)
    cenx = dissize / 2
    ceny = dissize / 2
    # pygame.draw.circle(gameDisplay,purple,(ux+x-CameraX,uy+y-CameraY),4)
    pygame.draw.line(gameDisplay, purple, (ux - CameraX, uy - CameraY), (ux + x - CameraX, uy + y - CameraY), 2)


def vending():
    pygame.draw.rect(gameDisplay, (255, 128, 0), [vendingx - CameraX, vendingy - CameraY, 50, 25])
    pygame.draw.rect(gameDisplay, (0, 128, 0), [vendingx - CameraX, vendingy - CameraY, 50, 25], width=10)




def game():
    global molespeed
    global teacherwalkspeed
    global teacheraccl
    global teacherrunspeed
    global keynum
    global boispeed
    global hasmessage
    global CameraX
    global CameraY
    trytochangepath = 0
    ihear = 0
    clapdistance = 1000
    boix = 1040
    boiy = 2480

    boivel = [0, 0]  # Magnitude and Direction

    molex = 1760
    moley = 3146
    moledir = 0
    canmerge = True

    # TEACHERSTUFF

    chasemode = False
    debugcoord = True
    pygame.mixer.music.set_volume(.1)
    pygame.mixer.music.play(-1)
    needtobounce = 0
    keystates = [0, 0, 0, 0, 0]  # Right Left Up Down lshift
    t = 0
    time_since_death = 0
    createpath = []

    Keylocations = [(1051, 2247), (1402, 2174), (1819, 2237), (1793, 2653), (1889, 3089), (1026, 3107), (1198, 1676), (1679, 908), (1708, 271), (767, 396), (251, 97), (184, 396), (179, 585), (173, 1032), (788, 911), (196, 1293), (181, 1617), (190, 1923), (236, 2373), (794, 1611), (851, 1826), (487, 2300)

                    ]
    # THERE ARE 22 locations, leave at least 2 for the students
    # CHOOSES KEYS LOCATIONS
    rkeyloc = []
    r.shuffle(Keylocations)

    rkeyloc = Keylocations[:keynum]
    # print(rkeyloc)

    chasing = 0

    oou = []
    fartface = [[0, 0]]
    returnmode = 0
    DOOR = [False, 0, 0]
    waittoupdate = 0
    standandscan = 10
    keycapturecount = 0
    needmorekeys = 0


    # pack
    money = 0

    delieverfrom, delieverto = movepackage(Keylocations, rkeyloc)
    # print(delieverfrom,delieverto)
    hasmessage = False
    accepting = False
    near = 0
    node_surface = pygame.Surface((dissize, dissize))

    teacher = Teacher(pathing_map, sight_map, teacherwalkspeed, teacherrunspeed)


    while True:

        t += 1
        time_since_death += 1

        if teacher.walkspeed < 80:  # Clapping
            if t % (int(80 / teacher.walkspeed)) == 0:
                clapdistance = yseful.cdistance(boix, boiy, teacher.x, teacher.y)

                volum = 10 / (clapdistance / 10)

                pygame.mixer.Sound.set_volume(clap_sound, volum)
                pygame.mixer.Sound.play(clap_sound)
        if 1 == r.randint(1, 1000):  # Coming for you sound effect
            volum = 10 / (clapdistance / 10)
            pygame.mixer.Sound.set_volume(comingfor_sound, volum)
            pygame.mixer.Sound.play(comingfor_sound)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print(createpath)
                pygame.quit()
                quit()
            keystates = yseful.basicinput(event, keystates)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                menu()

        # Movement
        # Boi
        bdir = []
        if keystates[0] == 1 and keystates[1] == 1:
            boivel = yseful.veladd(boivel, [0, 0])
        elif keystates[0] == 1 and keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 7 * m.pi / 4])
        elif keystates[0] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed, m.pi / 4])
        elif keystates[1] == 1 and keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 5 * m.pi / 4])
        elif keystates[1] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 3 * m.pi / 4])
        elif keystates[2] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [0, 0])

        elif keystates[0] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 0])
        elif keystates[1] == 1:
            boivel = yseful.veladd(boivel, [boispeed, m.pi])
        elif keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 3 * m.pi / 2])
        elif keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed, m.pi / 2])

        if keystates[4] == 0:
            boivel = yseful.veladd(boivel, [-.2 * boivel[0], boivel[1]])
        else:
            boivel = yseful.veladd(boivel, [-.4 * boivel[0], boivel[1]])

        boix += boivel[0] * m.cos(boivel[1])
        boiy += boivel[0] * m.sin(boivel[1])

        CXG = boix - dissize / 2
        CYG = boiy - dissize / 2

        CameraX -= (CameraX - CXG) / 20
        CameraY -= (CameraY - CYG) / 20

        teacher.update(boix, boiy, boivel, DOOR)

        # Collisions
        # DRAW STUFF HERE IF THEIR COLLISION'S MATTER
        gameDisplay.fill(white)
        dschool()
        vending()

        if needtobounce == 1:
            boix += -1.1 * boispeed * boivel[0] * m.cos(boivel[1])
            boiy += -1.1 * boispeed * boivel[0] * m.sin(boivel[1])
            boivel = [0, 0]

        boirightside = aiSurface.get_at((int(11 + boix), int(boiy)))
        if boirightside == (0, 0, 0) or boirightside == (255, 128, 0):
            boivel = yseful.veladd(boivel, [boispeed * 3, m.pi])
        if boirightside == (255, 0, 0) and keycapturecount < keynum:
            boivel = yseful.veladd(boivel, [boispeed * 3, m.pi])
            needmorekeys += +1

        if needmorekeys > 1:
            pygame.mixer.Sound.play(morekeys_sound)
            needmorekeys = -50

        boileftside = aiSurface.get_at((int(boix - 11), int(boiy)))
        if boileftside == (0, 0, 0) or boileftside == (255, 128, 0):
            boivel = yseful.veladd(boivel, [boispeed * 3, 0])

        boitopside = aiSurface.get_at((int(boix), int(boiy - 11)))
        if boitopside == (0, 0, 0) or boitopside == (255, 128, 0):
            boivel = yseful.veladd(boivel, [boispeed * 3, m.pi / 2])

        if (boirightside == (0, 0, 255) or boileftside == (0, 0, 255)) and pgt.cdistance(teacher.x, teacher.y, boix, boiy) < 1000:

            DOOR = [True, boix, boiy]
            standandscan = 0

        boidownside = aiSurface.get_at((int(boix), int(boiy + 11)))
        if boidownside == (0, 0, 0) or boidownside == (255, 128, 0):
            boivel = yseful.veladd(boivel, [boispeed * 3, 3 * m.pi / 2])


        # Collecting Keys
        for v in range(keynum):

            if yseful.cdistance(boix, boiy, rkeyloc[v][0], rkeyloc[v][1]) < 15:
                pygame.mixer.Sound.play(ding_sound)
                keycapturecount += 1
                rkeyloc[v] = (-500, -100)
                teacher.walkspeed += teacheraccl
                teacher.runspeed += teacheraccl
                if keycapturecount == keynum - 1:
                    pygame.mixer.Sound.play(onemore_sound)
                if keycapturecount == keynum:
                    pygame.mixer.Sound.play(outofhere_sound)

                    trytochangepath = 1

        # GETTING CAPTURED
        if yseful.cdistance(boix, boiy, teacher.x, teacher.y) < 50 and teacher.agro == 50:
            time_since_death = 0
            keycapturecount = 0
            r.shuffle(Keylocations)
            rkeyloc = Keylocations[:keynum]
            boix = 241
            boiy = 2260

            teacher.__init__(teacher.pathing_map, teacher.sight_map, 2, 4.1)
            CameraX = 241 - dissize / 2
            CameraY = 2368 - dissize / 2
            chasemode = False
            DOOR = [False, [0, 0]]
            pygame.mixer.Sound.play(detention_sound)
            delieverfrom, delieverto = movepackage(Keylocations, rkeyloc)
            hasmessage = False
            teacher.x = 188
            teacher.y = 1912
            teacher.return_to_route()
            canmerge = True
            trytochangepath = 0
            molex = 1760
            moley = 3146

        # ESCAPING
        if boiy > 2444 and boix < 950 and keycapturecount == keynum:
            victory()
            teacher.x = 1000
            teacher.y = 2000
        # DELIVERING MESSAGES
        if yseful.cdistance(boix, boiy, delieverfrom[0], delieverfrom[1]) < 30 and hasmessage == False and near == 0:
            pygame.mixer.Sound.play(deliver_sound)
            near = 1
            accepting = True

        if yseful.cdistance(boix, boiy, delieverto[0], delieverto[1]) < 30 and hasmessage == False and near == 0:
            pygame.mixer.Sound.play(iwant_sound)
            near = 1
        if yseful.cdistance(boix, boiy, delieverto[0], delieverto[1]) < 30 and hasmessage == True:
            pygame.mixer.Sound.play(thankyou_sound)
            near = 1
            hasmessage = False
            money += 1
            delieverfrom, delieverto = movepackage(Keylocations, rkeyloc)
        if yseful.cdistance(boix, boiy, delieverfrom[0], delieverfrom[1]) > 80 and yseful.cdistance(boix, boiy, delieverto[0], delieverto[1]) > 80 and yseful.cdistance(boix, boiy, vendingx, vendingy) > 120:
            accepting = False
            near = 0

        # BUYING ENERGY DRINK
        if yseful.cdistance(boix, boiy, vendingx, vendingy) < 80 and near == 0:
            near = 1
            if money < 2:
                pygame.mixer.Sound.play(ifihad_sound)
            if money >= 2 and boispeed < 2:
                pygame.mixer.Sound.play(yes_sound)
                money -= 2
                boispeed += .25

        # MOLE AI
        try:
            molecolor = aiSurface.get_at((int(molex), int(moley)))
        except IndexError:
            molecolor = 'offscreen'
        if molecolor == (0, 0, 0):
            showmole = False
            molego = molespeed / 2
        elif molecolor == 'offscreen':
            showmole = False
            molego = molespeed + .1
        else:
            showmole = True
            molego = molespeed + 0

        if yseful.cdistance(boix, boiy, molex, moley) < 10:
            teacher.status = teacher.get_status("chasing")
            teacher.agro = 50
            molego = 0

        moledir = m.atan2(boiy - moley, boix - molex)
        molex += molego * m.cos(moledir) * (1 + time_since_death/5000)
        moley += molego * m.sin(moledir) * (1 + time_since_death/5000)

        boi(boix, boiy)

        lines = [(teacher.x - CameraX, teacher.y - CameraY)] + [(p.x - CameraX, p.y - CameraY) for p in teacher.path]
        if len(lines) > 1:
            pygame.draw.lines(gameDisplay, red, False, lines)

        draw_teacher(teacher.x, teacher.y, teacher.agro, teacher.dir, boix, boiy)
        pgt.text(gameDisplay, (teacher.x - CameraX, teacher.y - CameraY), str(teacher.status.name), black, 20)

        if boix > 1890:
            boix = 1890
        if boix < 40:
            boix = 40
        if boiy > 3160:
            boiy = 3160
        if boiy < 40:
            boiy = 40

        # for v in lightballs:
        #     pygame.draw.circle(gameDisplay,(80,80,80),(v[0]-CameraX,v[1]-CameraY),20)
        keys(rkeyloc)



        boi(boix, boiy)

        otherstudent(delieverfrom[0], delieverfrom[1])
        otherstudent(delieverto[0], delieverto[1])
        if accepting == True and hasmessage == False:
            button('Accept?', delieverfrom[0] - 50 - CameraX, delieverfrom[1] - 25 - CameraY, 100, 50, green, bright_green, action=acceptsmessage)
        if hasmessage == True:
            arrow(boix, boiy, delieverto[0], delieverto[1])
        button('Money:' + str(money), dissize - 100, 0, 100, 50, yellow, yellow, action=None)
        button('Keys:' + str(keycapturecount) + "/" + str(keynum), dissize - 100, 50, 100, 50, orange, orange, action=None)
        if showmole:
            mole(molex, moley)

        fps = round(clock.get_fps(), 2)
        button(str(fps), 0, 0, 100, 50, yellow, yellow, action=None)

        pygame.display.update()
        # print(teacherwalkspeed,teacherrunspeed)
        clock.tick(60)


menu()
game()
