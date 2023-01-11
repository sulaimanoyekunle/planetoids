"""
Subcontroller module for Planetoids

This module contains the subcontroller to manage a single level (or wave) in the 
Planetoids game.  Instances of Wave represent a single level, and should correspond
to a JSON file in the Data directory. Whenever you move to a new level, you are 
expected to make a new instance of the class.

The subcontroller Wave manages the ship, the asteroids, and any bullets on screen. These 
are model objects. Their classes are defined in models.py.

Most of your work on this assignment will be in either this module or models.py.
Whether a helper method belongs in this module or models.py is often a complicated
issue.  If you do not know, ask on Ed Discussions and we will answer.

# Soul Oyekunle, sgo9
# December 7, 2022
"""
from game2d import *
from consts import *
from models import *
import random
import datetime

# PRIMARY RULE: Wave can only access attributes in models.py via getters/setters
# Level is NOT allowed to access anything in app.py (Subcontrollers are not permitted
# to access anything in their parent. To see why, take CS 3152)

class Wave(object):
    """
    This class controls a single level or wave of Planetoids.
    
    This subcontroller has a reference to the ship, asteroids, and any bullets on screen.
    It animates all of these by adding the velocity to the position at each step. It
    checks for collisions between bullets and asteroids or asteroids and the ship 
    (asteroids can safely pass through each other). A bullet collision either breaks
    up or removes a asteroid. A ship collision kills the player. 
    
    The player wins once all asteroids are destroyed.  The player loses if they run out
    of lives. When the wave is complete, you should create a NEW instance of Wave 
    (in Planetoids) if you want to make a new wave of asteroids.
    
    If you want to pause the game, tell this controller to draw, but do not update.  See
    subcontrollers.py from Lecture 25 for an example.  This class will be similar to
    than one in many ways.
    
    All attributes of this class are to be hidden. No attribute should be accessed 
    without going through a getter/setter first. However, just because you have an
    attribute does not mean that you have to have a getter for it. For example, the
    Planetoids app probably never needs to access the attribute for the bullets, so 
    there is no need for a getter there. But at a minimum, you need getters indicating
    whether you one or lost the game.
    """
    # LIST ANY ATTRIBUTES (AND THEIR INVARIANTS) HERE IF NECESSARY
    # THE ATTRIBUTES LISTED ARE SUGGESTIONS ONLY AND CAN BE CHANGED AS YOU SEE FIT
    # Attribute _data: The data from the wave JSON, for reloading 
    # Invariant: _data is a dict loaded from a JSON file
    #
    # Attribute _ship: The player ship to control 
    # Invariant: _ship is a Ship object
    #
    # Attribute _asteroids: the asteroids on screen 
    # Invariant: _asteroids is a list of Asteroid, possibly empty
    #
    # Attribute _bullets: the bullets currently on screen 
    # Invariant: _bullets is a list of Bullet, possibly empty
    #
    # Attribute _lives: the number of lives left 
    # Invariant: _lives is an int >= 0
    #
    # Attribute _firerate: the number of frames until the player can fire again 
    # Invariant: _firerate is an int >= 0
    
    # GETTERS AND SETTERS (ONLY ADD IF YOU NEED THEM)
    def getship(self):
        return self._ship

    def getdata(self):
        return self._data

    def getasteroid(self):
        return self._asteroid

    def getlives(self):
        return self._lives

    # INITIALIZER (standard form) TO CREATE SHIP AND ASTEROIDS
    def __init__(self, json):
        self._data = json
        self.create_ship(json)
        self._create_asteroid(json)
        self._lives = SHIP_LIVES
        self._bullets = []
        self._lastfire = 0

    # UPDATE METHOD TO MOVE THE SHIP, ASTEROIDS, AND BULLETS
    def update(self,input, dt):
        if self._ship is not None: 
            if input.is_key_down('left'):
                self._ship._turn_left()
            if input.is_key_down('right'):
                self._ship._turn_right()
            if input.is_key_down('up'):
                self._ship._impulse() 

            self._ship._moving()
            self._horizontal_deadzsone()
            self._vertical_deadzsone()
            self.create_bullet(input)
            self.create_collision()

        for i in range(len(self._asteroid)):   
            self._asteroid[i].astr_moving()   

            self._astro_horizontal_deadzsone(self._asteroid[i])
            self._astro_vertical_deadzsone(self._asteroid[i])

        for i in self._bullets:
            i._moving()
        
        self._delete_asteroids()
        self._delete_bullets()
        if self._ship is None:
            self._lives -= 1
        
    # DRAW METHOD TO DRAW THE SHIP, ASTEROIDS, AND BULLETS
    def draw(self,view):
        if self._ship is not None:
            self._ship.draw(view)
        
        for i in range(len(self._asteroid)):   
            self._asteroid[i].draw(view)  

        for i in range(len(self._bullets)): 
            self._bullets[i].draw(view)  
              
    # RESET METHOD FOR CREATING A NEW LIFE

    # HELPER METHODS FOR PHYSICS AND COLLISION DETECTION
    def create_ship(self, json):
        ship_data = json['ship']
        x = ship_data['position'][0]
        y = ship_data['position'][1]
        a = ship_data['angle']
        self._ship = Ship(x, y, a)

    def create_bullet(self, input):
        self._lastfire += 1
        if input.is_key_down('spacebar') and self._lastfire >= BULLET_RATE:
            vector = self._ship.getfacing() * SHIP_RADIUS
            x = vector.x + self._ship.x 
            y = vector.y + self._ship.y
            v = self._ship.getfacing() * BULLET_SPEED
            b = Bullet(x,y,v)
            self._bullets.append(b)
            self._lastfire = 0

    def create_collision(self): 
        for i in range(len(self._asteroid)):
            if self._ship is not None:
                w = SHIP_RADIUS + self._asteroid[i].width/2
                x = self._ship.x - self._asteroid[i].x
                y = self._ship.y - self._asteroid[i].y
                d = (x**2 + y**2)**0.5
                if w > d:
                    if self._ship.getvelocity() == introcs.Vector2(0,0):
                        v = self._ship.getfacing()
                    else: 
                        v = self._ship.getvelocity().normalize()
                    list = self._asteroid[i].resultant_vector(v)
                    v1 = list[0]
                    v2 = list[1]
                    if self._asteroid[i].width/2 == MEDIUM_RADIUS:
                        self.create_medium_asteroid(v, v1, v2, self._asteroid[i].x, self._asteroid[i].y)
                    elif self._asteroid[i].width/2 == LARGE_RADIUS:
                        self.create_large_asteroid(v, v1, v2, self._asteroid[i].x, self._asteroid[i].y)
                    self._ship = None
                    self._asteroid[i].setDestroyed(True)

        for i in range(len(self._asteroid)):
            if not self._asteroid[i].getnowdestroyed():
                for j in range(len(self._bullets)):
                    if not self._bullets[j].getnowdestroyed():
                        w = BULLET_RADIUS + self._asteroid[i].width/2
                        x = self._bullets[j].x - self._asteroid[i].x
                        y = self._bullets[j].y - self._asteroid[i].y
                        d = (x**2 + y**2)**0.5
                        if w > d:
                            v = self._bullets[j].getvelocity().normalize()
                            list = self._asteroid[i].resultant_vector(v)
                            v1 = list[0]
                            v2 = list[1]
                            if self._asteroid[i].width/2 == MEDIUM_RADIUS:
                                self.create_medium_asteroid(v, v1, v2, self._asteroid[i].x, self._asteroid[i].y)
                            elif self._asteroid[i].width/2 == LARGE_RADIUS:
                                self.create_large_asteroid(v, v1, v2, self._asteroid[i].x, self._asteroid[i].y)
                            self._bullets[j].setDestroyed(True)
                            self._asteroid[i].setDestroyed(True)      

    def create_medium_asteroid(self, v, v1, v2, x, y):
        x1 = SMALL_RADIUS * v.x + x
        x2 = SMALL_RADIUS * v1.x + x
        x3 = SMALL_RADIUS * v2.x + x

        y1 = SMALL_RADIUS * v.y + y
        y2 = SMALL_RADIUS * v1.y + y
        y3 = SMALL_RADIUS * v2.y + y

        ast = Asteroid(x1, y1, SMALL_RADIUS*2, SMALL_RADIUS*2, SMALL_IMAGE, v * SMALL_SPEED)
        self._asteroid.append(ast)

        ast1 = Asteroid(x2, y2, SMALL_RADIUS*2, SMALL_RADIUS*2, SMALL_IMAGE, v1 * SMALL_SPEED)
        self._asteroid.append(ast1)

        ast2 = Asteroid(x3, y3, SMALL_RADIUS*2, SMALL_RADIUS*2, SMALL_IMAGE, v2 * SMALL_SPEED)
        self._asteroid.append(ast2)

    def create_large_asteroid(self, v, v1, v2, x, y):
        x1 = MEDIUM_RADIUS * v.x + x
        x2 = MEDIUM_RADIUS * v1.x + x
        x3 = MEDIUM_RADIUS * v2.x + x

        y1 = MEDIUM_RADIUS * v.y + y
        y2 = MEDIUM_RADIUS * v1.y + y
        y3 = MEDIUM_RADIUS * v2.y + y

        ast = Asteroid(x1, y1, MEDIUM_RADIUS*2, MEDIUM_RADIUS*2, MEDIUM_IMAGE, v * MEDIUM_SPEED)
        self._asteroid.append(ast)

        ast1 = Asteroid(x2, y2, MEDIUM_RADIUS*2, MEDIUM_RADIUS*2, MEDIUM_IMAGE, v1 * MEDIUM_SPEED)
        self._asteroid.append(ast1)

        ast2 = Asteroid(x3, y3, MEDIUM_RADIUS*2, MEDIUM_RADIUS*2, MEDIUM_IMAGE, v2 * MEDIUM_SPEED)
        self._asteroid.append(ast2)

    def _horizontal_deadzsone(self):
        if self._ship.x < - DEAD_ZONE:
            self._ship.x += GAME_WIDTH + (2*DEAD_ZONE)
        if self._ship.x > GAME_WIDTH + DEAD_ZONE:
            self._ship.x -=  GAME_WIDTH + (2*DEAD_ZONE)

    def _vertical_deadzsone(self):
        if self._ship.y < - DEAD_ZONE:
            self._ship.y += GAME_HEIGHT + (2*DEAD_ZONE)
        if self._ship.y > GAME_HEIGHT + DEAD_ZONE:
            self._ship.y -=  GAME_HEIGHT + (2*DEAD_ZONE)

    def _create_asteroid(self, json):
        self._asteroid = []
        for i in range(len(json["asteroids"])):
            asteroid_data = json['asteroids'][i] 
            size = asteroid_data['size']
            x=asteroid_data['position'][0]
            y = asteroid_data['position'][1]
            d = asteroid_data['direction']
            vector = introcs.Vector2(d[0], d[1])
            vector.normalize()
            if size == LARGE_ASTEROID: 
                ast = Asteroid(x, y, LARGE_RADIUS*2, LARGE_RADIUS * 2, LARGE_IMAGE, vector * LARGE_SPEED)
            if size == MEDIUM_ASTEROID:
                ast = Asteroid(x, y, MEDIUM_RADIUS*2, MEDIUM_RADIUS*2, MEDIUM_IMAGE, vector * MEDIUM_SPEED)
            if size == SMALL_ASTEROID:
                ast = Asteroid(x, y, SMALL_RADIUS*2, SMALL_RADIUS*2, SMALL_IMAGE, vector * SMALL_SPEED)
            self._asteroid.append(ast)

    def _astro_horizontal_deadzsone(self, asteroid):
        if asteroid.x < - DEAD_ZONE:
            asteroid.x += GAME_WIDTH + (2*DEAD_ZONE)
        if asteroid.x > GAME_WIDTH + DEAD_ZONE:
            asteroid.x -=  GAME_WIDTH + (2*DEAD_ZONE)

    def _astro_vertical_deadzsone(self, asteroid):
        if asteroid.y < - DEAD_ZONE:
            asteroid.y += GAME_HEIGHT + (2*DEAD_ZONE)
        if asteroid.y > GAME_HEIGHT + DEAD_ZONE:
            asteroid.y -=  GAME_HEIGHT + (2*DEAD_ZONE)  
                
    def _delete_bullets(self):
        b = 0
        while b < len(self._bullets):
            if self._bullets[b].getnowdestroyed():
                del self._bullets[b]
            else:
                b += 1

    def _delete_asteroids(self):
        b = 0
        while b < len(self._asteroid):
            if self._asteroid[b].getnowdestroyed():
                del self._asteroid[b]
            else:
                b += 1

    

    


        






    

    

                


            











        



    