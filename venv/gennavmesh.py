import pygame
import yseful
import pathing
import math as m

pygame.init()
gameDisplay = pygame.display.set_mode((1000,1000))
schoolsee = pygame.image.load('school.png')
school = pygame.image.load('school.png')

aiSurface = pygame.Surface((1920,3200))
aiSurface.blit(school,(0,0))

white = (255,255,255)
black = (0,0,0)
red = (255,0,0)
blue = (0,0,255)
orange = (255,128,0)
green = (65,177,48)
dissize = 1000

CameraX = 500
CameraY = 500



clock = pygame.time.Clock()
def setpointwalls():
    scale = 1
    points = []
    for x in range(1920//scale):
        for y in range(3200//scale):
            rx = x*scale
            ry = y*scale
            if aiSurface.get_at((rx,ry)) == black or aiSurface.get_at((rx,ry)) == orange:
                edges = 0
                try:
                    if aiSurface.get_at((rx+scale,ry+scale)) == white:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry-scale)) == white:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry+scale)) == white:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry-scale)) == white:
                        edges += 1

                    if aiSurface.get_at((rx,ry+scale)) == white:
                        edges += 1
                    if aiSurface.get_at((rx,ry-scale)) == white:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry)) == white:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry)) == white:
                        edges += 1

                    if aiSurface.get_at((rx+scale,ry+scale)) == green:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry-scale)) == green:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry+scale)) == green:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry-scale)) == green:
                        edges += 1

                    if aiSurface.get_at((rx,ry+scale)) == green:
                        edges += 1
                    if aiSurface.get_at((rx,ry-scale)) == green:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry)) == green:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry)) == green:
                        edges += 1



                    if aiSurface.get_at((rx+scale,ry+scale)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry-scale)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry+scale)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry-scale)) == blue:
                        edges += 1

                    if aiSurface.get_at((rx,ry+scale)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx,ry-scale)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx-scale,ry)) == blue:
                        edges += 1
                    if aiSurface.get_at((rx+scale,ry)) == blue:
                        edges += 1



                except IndexError:
                    edge = 0
                if edges > 3 or edges == 1:
                    points.append((rx,ry,0))
    return(points)

def connectpoints():

    points = setpointwalls()
    lines = []

    for sta in range(len(points)):
        potent = [] #points that it 'can' draw a line to
        for des in range(len(points)):
            fail = False
            if des == sta:
                fail = True
            checkerx = points[sta][0]
            checkery = points[sta][1]
            direction = m.atan2(points[des][1]-points[sta][1],points[des][0]-points[sta][0])

            if direction % (m.pi/2) == 0:
                distance = yseful.cdistance(points[sta][0],points[sta][1],points[des][0],points[des][1])

                for v in range(int(distance//10)):
                    checkerx += m.cos(direction) * 10
                    checkery += m.sin(direction) * 10
                    col = aiSurface.get_at((int(checkerx),int(checkery)))
                    if col == white or col == green or col == blue:
                        fail = True
                        break

                if fail == False:
                    a = ([(points[des][0],points[des][1]),(points[sta][0],points[sta][1])] in lines == False)
                    #print(a)
                    if points[sta][2] < 2:
                        if [(points[sta][0],points[sta][1]),(points[des][0],points[des][1])] in lines or [(points[des][0],points[des][1]),(points[sta][0],points[sta][1])] in lines:#If both points have made less than two connections and the line does not already exist
                            continue
                        else:
                            lines.append([(points[sta][0],points[sta][1]),(points[des][0],points[des][1])]) #Create the line
                            points[sta] = (points[sta][0],points[sta][1],points[sta][2]+1) # Updating the connection number on each line
                            points[des] = (points[des][0],points[des][1],points[des][2]+1)






    return(lines,points)

def dschool():
    gameDisplay.blit(schoolsee,(0-CameraX,0-CameraY))
def run():
    global CameraX
    global CameraY
    keystates = [0,0,0,0,0]
    boivel = [0,0]
    boix = 500
    boiy = 500

    boispeed = 3


    lines,places = connectpoints()
    print(len(lines))
    print(len(places),"points")
    print(lines)
    with open('walls', 'w') as wal:
        for l in lines:
            tow = '[('+str(l[0][0])+'+'+str(l[0][1])+'),('+str(l[1][0])+'+'+str(l[1][1])+')]'
            if l != lines[-1]:
                wal.write(tow+'\n')
            else:
                wal.write(tow)
    while True:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            keystates = yseful.basicinput(event,keystates)

        #Movement
            #Boi
        bdir = []
        if keystates[0] == 1 and keystates[1] == 1:
            boivel = yseful.veladd(boivel, [0,0])
        elif keystates[0] == 1 and keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed,7*m.pi/4])
        elif keystates[0] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed,m.pi/4])
        elif keystates[1] == 1 and keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed,5*m.pi/4])
        elif keystates[1] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed,3*m.pi/4])
        elif keystates[2] == 1 and keystates[3] == 1:
            boivel = yseful.veladd(boivel, [0,0])

        elif keystates[0] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 0])
        elif keystates[1] == 1:
            boivel = yseful.veladd(boivel, [boispeed, m.pi])
        elif keystates[2] == 1:
            boivel = yseful.veladd(boivel, [boispeed, 3*m.pi/2])
        elif keystates[3] == 1:
            boivel = yseful.veladd(boivel, [boispeed, m.pi/2])



        if keystates[4] == 0:
            boivel = yseful.veladd(boivel, [-.2*boivel[0],boivel[1]])
        else:
            boivel = yseful.veladd(boivel, [-.4 * boivel[0], boivel[1]])

        boix += boivel[0] * m.cos(boivel[1])
        boiy += boivel[0] * m.sin(boivel[1])

        CXG = boix - dissize/2
        CYG = boiy - dissize/2

        CameraX -= (CameraX - CXG)/2
        CameraY -= (CameraY - CYG)/2

        gameDisplay.fill(white)
        dschool()

        for p in places:
            if p[2] == 3:
                pygame.draw.circle(gameDisplay, (255,255,0), (p[0] - CameraX, p[1] - CameraY), 4)
            elif p[2] == 2:
                pygame.draw.circle(gameDisplay,red,(p[0]-CameraX,p[1]-CameraY),4)
            elif p[2] == 1:
                pygame.draw.circle(gameDisplay, blue, (p[0] - CameraX, p[1] - CameraY), 4)
            else:
                pygame.draw.circle(gameDisplay, green, (p[0] - CameraX, p[1] - CameraY), 4)

        for l in lines:
            pygame.draw.line(gameDisplay,red,(l[0][0]-CameraX,l[0][1]-CameraY),(l[1][0]-CameraX,l[1][1]-CameraY),2)

        pygame.draw.circle(gameDisplay, blue, (1920 - CameraX, 3200 - CameraY), 3)

        pygame.display.update()
        clock.tick(60)


run()