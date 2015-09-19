# Eric Terui + Eterui + Section H
import random
import pyaudio
from Tkinter import *
import wave
import numpy as np


# Animation class taken from Kosbie's lecture and notes
###########################################
# Animation class
###########################################

class Animation(object):
    # Override these methods when creating your own animation
    def mousePressed(self, event): pass
    def keyPressed(self, event): pass
    def timerFired(self): pass
    def init(self): pass
    def redrawAll(self): pass
    
    # Call app.run(width,height) to get your app started
    def run(self, width=1167, height=690):
        # create the root and the canvas
        self.root = Tk()
        self.root.resizable(width=FALSE, height=FALSE)
        self.canvasWidth = width
        self.canvasHeight = height
        self.canvas = Canvas(self.root, width=width, height=height)
        self.canvas.pack()
        # set up events
        def redrawAllWrapper():
            self.redrawAll()
        def mousePressedWrapper(event):
            self.mousePressed(event)
        def keyPressedWrapper(event):
            self.keyPressed(event)
        self.root.bind("<Button-1>", mousePressedWrapper)
        self.root.bind("<Key>", keyPressedWrapper)
        # set up timerFired events
        self.timerFiredDelay = 10 # milliseconds
        def timerFiredWrapper():
            self.timerFired()
            # pause, then call timerFired again
            self.canvas.after(self.timerFiredDelay, timerFiredWrapper)
        # init and get timerFired running
        self.init()
        timerFiredWrapper()
        self.root.mainloop()

class Game(Animation):
    def mousePressed(self, event):
        if self.isStartScreen == True:
            self.startScreenMousePressed(event)
        elif self.isInstructionsScreen == True:
            self.instructionsScreenMousePressed(event)
        elif self.isPauseScreen == True:
            self.pauseScreenMousePressed(event)

    def startScreenMousePressed(self, event): # mousepressed for startScreen
        startButtonLeft = 440
        startButtonTop = 425
        startButtonRight = 760
        startButtonBot = 457
        # start game button
        if ((event.x <= startButtonRight) and (event.x >= startButtonLeft) and
            (event.y <= startButtonBot) and (event.y >= startButtonTop)):
            self.isStartScreen = False
            self.isGameOn = True
            self.drawGameDrawings()
            self.initPitchDetect()
        instructionsButtonLeft = 440
        instructionsButtonTop = 462
        instructionsButtonRight = 825
        instructionsButtonBot = 495
        # instructions button
        if ((event.x <= instructionsButtonRight) and
            (event.x >= instructionsButtonLeft) and
            (event.y <= instructionsButtonBot) and
            (event.y >= instructionsButtonTop)):
            self.isInstructionsScreen = True
            self.isStartScreen = False
            self.drawInstructionsScreen()
            self.canvas.delete("startScreen")

    def instructionsScreenMousePressed(self, event):
        backButtonLeft = 20
        backButtonTop = 10
        backButtonRight = 150
        backButtonBot = 90
        # back button
        if ((event.x <= backButtonRight) and (event.x >= backButtonLeft) and
            (event.y <= backButtonBot) and (event.y >= backButtonTop)):
            self.isStartScreen = True
            self.isInstructionsScreen = False
            self.drawStartScreen()
            self.canvas.delete("instructionsScreen")
        fMajButtonLeft = 255
        fMajButtonTop = 500
        fMajButtonRight = 905
        fMajButtonBot = 525
        # F Major Scale button
        if ((event.x <= fMajButtonRight) and (event.x >= fMajButtonLeft) and
            (event.y <= fMajButtonBot) and (event.y >= fMajButtonTop)):
            self.play_pyaudio("sounds/fMajor.wav") # plays wav file

    def pauseScreenMousePressed(self, event):
        resumeButtonLeft = 1055
        resumeButtonTop = 20
        resumeButtonRight = 1145
        resumeButtonBot = 70
        # Resume Button
        if ((event.x <= resumeButtonRight) and
            (event.x >= resumeButtonLeft) and
            (event.y <= resumeButtonBot) and (event.y >= resumeButtonTop)):
            self.canvas.delete("pauseScreen")
            self.isGameOn = True
            self.isPauseScreen = False

    def keyPressed(self, event):
        if event.keysym == "Up": # moves mario up a lane
            if self.mario.lane < 7: # upper bound
                self.mario.move(self.mario.lane + 1)
        elif event.keysym == "Down": # moves down a lane
            if self.mario.lane > 1: # lower bound
                self.mario.move(self.mario.lane - 1)
        elif event.keysym == "p": # pauses
            if self.isGameOn == True:
                self.isPauseScreen = True
                self.isGameOn = False
                self.drawPauseScreen()
        elif event.keysym == "r": # restarts
            self.init()
        elif event.keysym == "space": # shoots fireball
            if self.isGameOn == True:
                self.spawnMarioFireball()
        elif event.keysym == "s": # skip to boss fight
            if (self.isGameOn == True) and (self.isBossFight == False):
                self.startBossFight()

    # http://people.csail.mit.edu/hubert/pyaudio/#examples
    def play_pyaudio(self, mediaFile): # plays wav file
        chunk = 1024
        wf = wave.open(mediaFile, 'rb')
        p = pyaudio.PyAudio()
        # open stream
        stream = p.open(format =
                    p.get_format_from_width(wf.getsampwidth()),
                        channels = wf.getnchannels(),
                        rate = wf.getframerate(),
                        output = True)
        # read data
        data = wf.readframes(chunk)
        # play stream
        while data != '':
            stream.write(data)
            data = wf.readframes(chunk)
        stream.stop_stream()
        stream.close()
        p.terminate()

    # modified code from http://people.csail.mit.edu/hubert/pyaudio/#examples
    # modified to simply open a micStream
    def initPitchDetect(self): # starts micStream
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.p = pyaudio.PyAudio()
        self.micStream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

    # http://stackoverflow.com/questions/2648151/python-frequency-detection
    # modified to do take frames directly instead of reading wav file
    def doPitchDetect(self):
        self.frames = []
        # play stream and find the frequency of each chunk
        swidth = 2
        window = np.blackman(self.CHUNK)
        data = self.micStream.read(self.CHUNK)
        self.frames.append(data)
        # unpack the data and times by the hamming window
        indata = np.array(wave.struct.unpack("%dh"%(len(data)/swidth),
            data))*window
        # Take the fft and square each value
        fftData=abs(np.fft.rfft(indata))**2
        # find the maximum
        which = fftData[1:].argmax() + 1
        # use quadratic interpolation around the max
        if which != len(fftData)-1:
            y0,y1,y2 = np.log(fftData[which-1:which+2:])
            x1 = (y2 - y0) * .5 / (2 * y1 - y2 - y0)
            # find the frequency
            theFreq = (which+x1)*self.RATE/self.CHUNK/2
            if (theFreq > 300 and theFreq < 715):
                self.checkFreq(theFreq)
        else:
            theFreq = which*self.RATE/self.CHUNK/2
            if (theFreq > 300 and theFreq < 715):
                self.checkFreq(theFreq)

    def checkFreq(self, theFreq):
        closest = 0
        # finds closest freq in self.frequencies to theFreq
        for i in xrange(len(self.frequencies)):
            if (abs(self.frequencies[i] - theFreq) < abs(closest - theFreq)):
                closest = self.frequencies[i]
        if (closest == self.frequencies[0]): # low F 349.228 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["F", "F", "F"]): # 3 consecutive F's to move (for stability)
                self.mario.move(1)
                self.displayNote = "F"
            if self.lastNotes[-1] == "F": # if last freq was "F"
                self.lastNotes.append("F")
            else:
                self.lastNotes = ["F"] # if last freq wasn't "F"
        elif (closest == self.frequencies[1]): # G 391.995 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["G", "G", "G"]):
                self.mario.move(2)
                self.displayNote = "G"
            if self.lastNotes[-1] == "G":
                self.lastNotes.append("G")
            else:
                self.lastNotes = ["G"]
        elif (closest == self.frequencies[2]): # A 440.0 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["A", "A", "A"]):
                self.mario.move(3)
                self.displayNote = "A"
            if self.lastNotes[-1] == "A":
                self.lastNotes.append("A")
            else:
                self.lastNotes = ["A"]
        elif (closest == self.frequencies[3]): # B-Flat 466.164 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["B-Flat", "B-Flat", "B-Flat"]):
                self.mario.move(4)
                self.displayNote = "B-Flat"
            if self.lastNotes[-1] == "B-Flat":
                self.lastNotes.append("B-Flat")
            else:
                self.lastNotes = ["B-Flat"]
        elif (closest == self.frequencies[4]): # C 523.251 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["C", "C", "C"]):
                self.mario.move(5)
                self.displayNote = "C"
            if self.lastNotes[-1] == "C":
                self.lastNotes.append("C")
            else:
                self.lastNotes = ["C"]
        elif (closest == self.frequencies[5]): # D 587.330 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["D", "D", "D"]):
                self.mario.move(6)
                self.displayNote = "D"
            if self.lastNotes[-1] == "D":
                self.lastNotes.append("D")
            else:
                self.lastNotes = ["D"]
        elif (closest == self.frequencies[6]): # E 659.255 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["E", "E", "E"]):
                self.mario.move(7)
                self.displayNote = "E"
            if self.lastNotes[-1] == "E":
                self.lastNotes.append("E")
            else:
                self.lastNotes = ["E"]
        elif (closest == self.frequencies[7]): # High F 698.456 Hz
            if (self.lastNotes[len(self.lastNotes)-3:len(self.lastNotes)] ==
            ["High F", "High F", "High F"]):
                self.spawnMarioFireball()
                self.displayNote = "High F"
            if self.lastNotes[-1] == "High F":
                self.lastNotes.append("High F")
            else:
                self.lastNotes = ["High F"]

    def init(self):
        self.initGameStates()
        self.initImages()
        self.initMario()
        self.initObjects()
        self.initNotes()
        self.initCounters()
        self.drawStartScreen()

    def initGameStates(self):
        self.isStartScreen = True
        self.isInstructionsScreen = False
        self.isPauseScreen = False
        self.isGameOver = False
        self.isGameOn = False
        self.isBossFight = False

    def initMario(self):
        self.marioLane = 1 # bottom lane
        self.lives = 3
        self.lifeIcons = []
        self.mario = Mario(self.canvas, self.marioLane,
            self.staffTop, self.staffImg.height())

    def initObjects(self):
        self.flowerText = 0
        self.scoreText = 0
        self.score = 0
        self.goombas = []
        self.coins = []
        self.bowserFireballs = []
        self.fireFlowers = []
        self.marioFireballs = []
        self.nextCoinLane = random.randint(1, 7)

    def initCounters(self):
        self.gameTimerCount = 0
        self.bossTimerCount = 0
        self.storedFireballCount = 0
        self.marioFireballCooldown = 50
        self.previousFireballTime = 0

    def initNotes(self):
        self.frequencies = [349.228, 391.995, 440.0, 466.164, 523.251,
            587.330, 659.255, 698.456]
        self.lastNotes = ["F"]
        self.displayNote = "F"


    # staff drawn on MS paint
    # start screen edited from:
    # http://wiiuandmii.com/wp-content/uploads/2011/09/Super-Mario-Bros.jpg
    # background and mario taken from google image search
    # pause screen, instruction screen, game over, and win images edited from:
    # google image search
    def initImages(self):
        self.startScreenImage = PhotoImage(file="images/startScreen.gif")
        self.instructionsScreenImage = PhotoImage(file=
            "images/instructionsScreen.gif")
        self.pauseScreenImage = PhotoImage(file="images/pauseScreen.gif")
        self.gameOverScreenImage = PhotoImage(file=
            "images/gameOverScreen.gif")
        self.winScreenImage = PhotoImage(file="images/winScreen.gif")
        self.staffImg = PhotoImage(file="images/musicStaff.gif") # staff
        self.backgroundImg = PhotoImage(file="images/background.gif")
        self.marioLivesImg = PhotoImage(file="images/marioLives.gif")
        self.storedFlowersImg = PhotoImage(file="images/storedFlowers.gif")
        self.storedCoinsImg = PhotoImage(file="images/storedCoins.gif")
        self.staffMargin = 50
        self.staffTop = (self.canvasHeight - self.staffMargin -
            self.staffImg.height())
        self.staffLeft = 0
        self.staffBackgroundTop = (self.canvasHeight -
            (self.staffMargin * 2) - self.staffImg.height())

    def drawStartScreen(self):
        self.canvas.create_image(0, 0, image=self.startScreenImage,
            anchor="nw", tag="startScreen")

    def drawInstructionsScreen(self):
        self.canvas.create_image(0, 0, image=self.instructionsScreenImage,
            anchor="nw", tag="instructionsScreen")

    def drawPauseScreen(self):
        self.canvas.create_image(0, 0, image=self.pauseScreenImage,
            anchor="nw", tag="pauseScreen")

    def drawGameOverScreen(self):
        self.canvas.create_image(0, 0, image=self.gameOverScreenImage,
            anchor="nw", tag="gameOverScreen")

    def drawWinScreen(self):
        self.canvas.create_image(0, 0, image=self.winScreenImage,
            anchor = "nw", tag="winScreen")

    def drawGameDrawings(self):
        self.drawGameBackground()
        self.mario.draw()
        self.drawLives()
        self.drawScore()
        self.drawStoredFlowers()
        self.drawNoteLetter()

    def updateGameDrawings(self):
        for goomba in self.goombas:
            goomba.updateDrawing()
        for coin in self.coins:
            coin.updateDrawing()
        for marioFireball in self.marioFireballs:
            marioFireball.updateDrawing()
        self.scoreText = "x%d" % (self.score)
        self.flowerText = "x%d" % (self.storedFireballCount)
        self.canvas.itemconfig("score", text=self.scoreText)
        self.canvas.itemconfig("flowers", text=self.flowerText)
        self.canvas.itemconfig("note", text="Last Note: " + self.displayNote)
        self.mario.updateDrawing()

    def drawGameBackground(self):
        staffXValue = 0
        staffYValue = (self.canvasHeight - self.staffMargin -
            self.staffImg.height())
        self.canvas.create_image(0, 0, image = self.backgroundImg,
            anchor="nw")
        self.canvas.create_image(staffXValue, staffYValue,
            image = self.staffImg, anchor="nw")
        pauseText = "Press P to Pause"
        pauseSize = 10
        pauseX = self.canvasWidth * .90
        pauseY = self.canvasHeight / 50
        self.canvas.create_text(pauseX, pauseY, text=pauseText,
            font=("EMULOGIC", pauseSize), fill="white")

    def drawLives(self):
        fontX = self.canvasWidth / 11
        fontY = self.canvasHeight / 20
        fontSize = 10
        text = "Lives: "
        self.canvas.create_text(fontX, fontY, text=text, anchor="e",
            font=("EMULOGIC", fontSize), fill="white")
        iconMargin = self.marioLivesImg.width() / 4 # space between images
        iconX = fontX + iconMargin
        iconY = fontY
        for icon in xrange(self.lives - 1): # only shows extra lives
            nextIcon = self.canvas.create_image(iconX, iconY,
                image=self.marioLivesImg, anchor="w")
            self.lifeIcons.append(nextIcon)
            iconX += self.marioLivesImg.width() + iconMargin

    def drawStoredFlowers(self):
        iconMargin = self.storedFlowersImg.width() / 4
        iconX = self.canvasWidth / 15
        iconY = self.canvasHeight / 20 + 50
        fontSize = 10
        self.canvas.create_image(iconX, iconY, image=self.storedFlowersImg,
            anchor="e")
        fontX = iconX + iconMargin
        fontY = iconY
        self.canvas.create_text(fontX, fontY, text=self.flowerText,
            anchor="w", font=("EMULOGIC", fontSize), tag="flowers",
            fill="white")


    def drawScore(self):
        iconMargin = self.storedCoinsImg.width() / 4
        iconX = (self.canvasWidth * 0.90)
        iconY = self.canvasHeight / 14
        fontSize = 10
        # coin image
        self.canvas.create_image(iconX, iconY, image=self.storedCoinsImg,
            anchor="e")
        fontX = iconX + iconMargin
        fontY = iconY
        # num of coins
        self.canvas.create_text(fontX, fontY, text=self.scoreText,
            anchor="w", font=("EMULOGIC", fontSize), tag="score",
            fill="white")

    def drawNoteLetter(self):
        yValue = self.canvasWidth / 2
        xValue = self.canvasWidth / 50
        fontSize = 16
        text = self.displayNote
        # last note played
        self.canvas.create_text(yValue, xValue, text=text,
            font=("EMULOGIC", fontSize), tag="note", fill="white")
        
    def spawnRandomGoomba(self):
        self.nextGoombaLane = random.randint(1, 7) # 7 lanes available
        if self.nextGoombaLane == self.nextCoinLane: # no overlap
            if self.nextGoombaLane == 7: # upper bound
                self.nextGoombaLane -= 1
            else:
                self.nextGoombaLane += 1
        nextGoomba = Goomba(self.canvas, self.nextGoombaLane,
            self.canvasWidth, self.staffTop, self.staffImg.height())
        nextGoomba.draw()
        self.goombas.append(nextGoomba)

    def spawnNextCoin(self):
        # coins spawn within 2 lanes of previous coin
        self.nextCoinLane = random.randint(max(1, self.nextCoinLane - 2),
        min(7, self.nextCoinLane + 2)) # 7 lanes available
        nextCoin = Coin(self.canvas, self.nextCoinLane, self.canvasWidth,
            self.staffTop, self.staffImg.height())
        nextCoin.draw()
        self.coins.append(nextCoin)

    def checkGoombaPosition(self): # checks goomba collision
        for goomba in self.goombas:
            if goomba.xValue < 0: # off screen
                self.canvas.delete(goomba.drawing)
                self.goombas.remove(goomba)
            if goomba.lane == self.mario.lane: # hits mario
                if ((goomba.xValue <= self.mario.xValue+self.mario.width) and
                    (goomba.xValue >= self.mario.xValue)):
                    self.lives -= 1
                    if len(self.lifeIcons) > 0: # if lives still remaining
                        self.canvas.delete(self.lifeIcons.pop())
                    self.canvas.delete(goomba.drawing)
                    self.goombas.remove(goomba)

    def checkCoinPosition(self): # checks coin collision
        for coin in self.coins:
            if coin.xValue < 0: # off screen
                self.canvas.delete(coin.drawing)
                self.coins.remove(coin)
            if coin.lane == self.mario.lane: # coin hits mario
                if ((coin.xValue <= self.mario.xValue + self.mario.width) and
                    (coin.xValue >= self.mario.xValue)):
                    self.score += 1
                    self.canvas.delete(coin.drawing)
                    self.coins.remove(coin)

    def checkBowserFireballPosition(self): # checks bowserFireball collision
        for bowserFireball in self.bowserFireballs:
            if bowserFireball.xValue < 0: # off screen
                self.bowserFireballs.remove(bowserFireball)
                self.canvas.delete(bowserFireball.drawing)
            if bowserFireball.lane == self.mario.lane:
                if ((bowserFireball.xValue <= # hits mario
                    self.mario.xValue + self.mario.width) and
                    (bowserFireball.xValue >= self.mario.xValue)):
                    self.lives -= 1
                    if len(self.lifeIcons) > 0:
                        self.canvas.delete(self.lifeIcons.pop())
                    self.canvas.delete(bowserFireball.drawing)
                    self.bowserFireballs.remove(bowserFireball)

    def checkMarioFireballPosition(self): # checks marioFireball collision
        for marioFireball in self.marioFireballs:
            if marioFireball.xValue > self.canvasWidth: # off screen
                self.marioFireballs.remove(marioFireball)
                self.canvas.delete(marioFireball.drawing)
            # fireball in a lane occupied by bowser
            if (abs(marioFireball.lane - self.bowser.lane) <= 1):
                if ((marioFireball.xValue >= self.bowser.xValue) and
                    (marioFireball.xValue <=
                    self.bowser.xValue + self.bowser.width)): # hits bowser
                    self.bowser.health -= 1
                    self.canvas.delete(marioFireball.drawing)
                    self.marioFireballs.remove(marioFireball)
                    if self.bowser.health <= 0:
                        self.gameWon()

    def checkFireFlowerPosition(self): # checks fireFlower collision
        for fireFlower in self.fireFlowers:
            if fireFlower.xValue < 0: # fireFlower passes left edge of screen
                self.canvas.delete(fireFlower.drawing)
                self.fireFlowers.remove(fireFlower)
            if fireFlower.lane == self.mario.lane:
                if ((fireFlower.xValue <= self.mario.xValue +
                    self.mario.width) and (fireFlower.xValue >=
                    self.mario.xValue)): # fireFlower hits mario
                    self.storedFireballCount += 1
                    self.canvas.delete(fireFlower.drawing)
                    self.fireFlowers.remove(fireFlower)

    def spawnFireFlower(self):
        # coins spawn within 2 lanes of previous coin
        self.nextFireFlowerLane = random.randint(1, 7) # 7 lanes available
        nextFireFlower = FireFlower(self.canvas, self.nextFireFlowerLane,
            self.canvasWidth, self.staffTop, self.staffImg.height(),
            self.bowser.xValue)
        nextFireFlower.draw()
        self.fireFlowers.append(nextFireFlower)

    def gameWon(self):
        self.isGameOn = False
        self.canvas.delete(ALL)
        self.drawWinScreen()
        self.micStream.stop_stream()
        self.micStream.close()
        self.p.terminate()

    def gameOver(self):
        self.isGameOver = True
        self.canvas.delete(ALL)
        self.drawGameOverScreen()
        self.micStream.stop_stream()
        self.micStream.close()
        self.p.terminate()

    def startBossFight(self):
        self.isBossFight = True
        self.bowserLane = 2
        self.bowser = Bowser(self.canvas, self.bowserLane,
            self.staffTop, self.staffImg.height(), self.canvasWidth)
        self.drawBossFightDrawings()

    def drawBossFightDrawings(self):
        self.bowser.draw()
        self.drawBowserHealthbar()

    def drawBowserHealthbar(self):
        yMargin = 15
        x0 = self.bowser.xValue
        y0 = (self.bowser.yValue - self.bowser.image.height()/2 - 
            yMargin)
        x1 = (self.bowser.xValue - yMargin + (self.bowser.image.width() *
            (self.bowser.health / self.bowser.startHealth))) # %hp left
        y1 = self.bowser.yValue - self.bowser.image.height()/2
        self.bowserHealthbar = self.canvas.create_rectangle(x0, y0, x1, y1,
            fill="red", outline = "")

    def updateBowserHealthbar(self):
        yMargin = 15
        x0 = self.bowser.xValue
        y0 = (self.bowser.yValue - self.bowser.image.height()/2 - 
            yMargin)
        x1 = (self.bowser.xValue - yMargin + (self.bowser.image.width() *
            (self.bowser.health / self.bowser.startHealth))) # %hp left
        y1 = self.bowser.yValue - self.bowser.image.height()/2
        self.canvas.coords(self.bowserHealthbar, x0, y0, x1, y1)


    def updateBossDrawings(self):
        for bowserFireball in self.bowserFireballs:
            bowserFireball.updateDrawing()
        for fireFlower in self.fireFlowers:
            fireFlower.updateDrawing()
        self.bowser.updateDrawing()
        self.updateBowserHealthbar()

    def timerFired(self):
        if (self.isGameOn == True and self.isGameOver == False):
            self.updateGameDrawings()
            self.gameTimerCount += 1
            if ((self.gameTimerCount % 50 == 0) and
                (self.isBossFight == False)): # spawns goomba and coin
                self.spawnNextCoin()
                self.spawnRandomGoomba()
            for goomba in self.goombas:
                goomba.move()
            for coin in self.coins:
                coin.move()
            for marioFireball in self.marioFireballs:
                marioFireball.move()
            self.checkGoombaPosition()
            self.checkCoinPosition()
            self.doPitchDetect()
            if self.isBossFight == True:
                self.bossTimerFired()
            if self.lives <= 0: # game over if run out of lives
                self.gameOver()
            if (self.score == 20) and (self.isBossFight == False):
                self.startBossFight() # starts fight if score hits 20

    def bossTimerFired(self): # bossFight specific
        moveInterval = 150
        shootInterval = 100
        flowerInterval = 175
        self.bossTimerCount += 1
        self.updateBossDrawings()
        if self.bossTimerCount % moveInterval == 0:
            self.nextBowserLane = random.randint(1, 3) * 2 # 2, 4, or 6
            self.bowser.move(self.nextBowserLane)
        if self.bossTimerCount % shootInterval == 0:
            self.spawnBowserFireball(self.bowser.lane)
            self.spawnBowserFireball(self.bowser.lane - 1)
            self.spawnBowserFireball(self.bowser.lane + 1)
        if self.bossTimerCount % flowerInterval == 15:
            self.spawnFireFlower()
        for bowserFireball in self.bowserFireballs:
            bowserFireball.move()
        for fireFlower in self.fireFlowers:
            fireFlower.move()
        self.checkBowserFireballPosition()
        self.checkFireFlowerPosition()
        self.checkMarioFireballPosition()

    def spawnBowserFireball(self, lane):
        nextBowserFireball = BowserFireball(self.canvas, lane,
            self.canvasWidth, self.staffTop, self.staffImg.height(),
            self.bowser.xValue)
        nextBowserFireball.draw()
        self.bowserFireballs.append(nextBowserFireball)

    def spawnMarioFireball(self):
        if self.storedFireballCount > 0: # if fireballs stored
            if ((self.gameTimerCount - self.previousFireballTime) >
                self.marioFireballCooldown): # fireball cooldown
                self.previousFireballTime = self.gameTimerCount
                self.storedFireballCount -= 1
                lane = self.mario.lane # spawns from mario's current lane
                nextMarioFireball = MarioFireball(self.canvas, lane, self.mario.xValue,
                    self.staffTop, self.staffImg.height())
                nextMarioFireball.draw()
                self.marioFireballs.append(nextMarioFireball)
        

class Mario(object):
    def __init__(self, canvas, lane, staffTop, staffHeight):
        self.canvas = canvas
        self.lane = lane
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.numLanes = 8 # number of spaces in staff
        self.staffSpacing = self.staffHeight / self.numLanes
        self.xValue = 50
        # image taken from google image search
        self.image = PhotoImage(file = "images/mario.gif")
        self.width = self.image.width()
        self.spacing = self.staffHeight / self.numLanes
        self.yValue = (self.staffTop + self.staffHeight -
            (self.lane * self.spacing))

    def updateDrawing(self):
        self.canvas.coords(self.mario, self.xValue, self.yValue)

    def draw(self):
        self.mario = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def move(self, nextLane):
        self.lane = nextLane
        self.yValue = (self.staffTop + self.staffHeight -
            (self.lane * self.spacing))

# image taken from (both lines):
# http://24.media.tumblr.com/9e8af7c64018ea841425d9553a027ee6/
# tumblr_mimvgmGqph1rvo33yo1_250.gif
class Bowser(object):
    def __init__(self, canvas, lane, staffTop, staffHeight, canvasWidth):
        self.canvas = canvas
        self.lane = lane
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.numLanes = 8 # number of spaces in staff
        self.staffSpacing = self.staffHeight / self.numLanes
        self.image = PhotoImage(file = "images/bowser.gif")
        self.width = self.image.width()
        self.spacing = self.staffHeight / self.numLanes
        self.xValue = canvasWidth - self.image.width()
        self.yValue = (self.staffTop + self.staffHeight -
            (self.lane * self.spacing))
        self.health = self.startHealth = 6.0

    def updateDrawing(self):
        self.canvas.coords(self.bowser, self.xValue, self.yValue)

    def draw(self):
        self.bowser = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image, anchor = "w")

    def move(self, nextLane):
        self.lane = nextLane
        self.yValue = (self.staffTop + self.staffHeight -
            (self.lane * self.spacing))

class Goomba(object):
    def __init__(self, canvas, lane, canvasWidth, staffTop, staffHeight):
        self.canvas = canvas
        self.canvasWidth = canvasWidth
        self.lane = lane
        self.xValue = self.canvasWidth
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.image = PhotoImage(file="images/goomba.gif")
        self.setYValue()

    def setYValue(self):
        numLanes = 8 # number of lanes in staff
        spacing = self.staffHeight / numLanes
        self.yValue = self.staffTop + self.staffHeight - (self.lane * spacing)

    def draw(self):
        self.drawing = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def updateDrawing(self):
        self.canvas.coords(self.drawing, self.xValue, self.yValue)

    def move(self):
        self.xValue -= 5

class Coin(object):
    def __init__(self, canvas, lane, canvasWidth, staffTop, staffHeight):
        self.canvas = canvas
        self.canvasWidth = canvasWidth
        self.lane = lane
        self.xValue = self.canvasWidth
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.image = PhotoImage(file="images/coin.gif")
        self.setYValue()

    def setYValue(self):
        numLanes = 8 # number of lanes in staff
        spacing = self.staffHeight / numLanes
        self.yValue = self.staffTop + self.staffHeight - (self.lane * spacing)

    def draw(self):
        self.drawing = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def updateDrawing(self):
        self.canvas.coords(self.drawing, self.xValue, self.yValue)

    def move(self):
        self.xValue -= 5

# image from http://www.pixeljoint.com/files/icons/full/fireballz.gif
class BowserFireball(object):
    def __init__(self, canvas, lane, canvasWidth, staffTop,
        staffHeight, xValue):
        self.canvas = canvas
        self.canvasWidth = canvasWidth
        self.lane = lane
        self.xValue = xValue
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.image = PhotoImage(file="images/bowserFireball.gif")
        self.setYValue()

    def setYValue(self):
        numLanes = 8
        spacing = self.staffHeight / numLanes
        self.yValue = self.staffTop + self.staffHeight - (self.lane * spacing)

    def draw(self):
        self.drawing = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def updateDrawing(self):
        self.canvas.coords(self.drawing, self.xValue, self.yValue)

    def move(self):
        self.xValue -= 5

# image taken from:
# http://www.mariomayhem.com/downloads/sprites/smb1/smb_items_sheet.png
class FireFlower(object):
    def __init__(self, canvas, lane, canvasWidth, staffTop, staffHeight,
        xValue):
        self.canvas = canvas
        self.canvasWidth = canvasWidth
        self.lane = lane
        self.xValue = xValue
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.image = PhotoImage(file="images/fireFlower.gif")
        self.setYValue()

    def setYValue(self):
        numLanes = 8 # number of lanes in staff
        spacing = self.staffHeight / numLanes
        self.yValue = self.staffTop + self.staffHeight - (self.lane * spacing)

    def draw(self):
        self.drawing = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def updateDrawing(self):
        self.canvas.coords(self.drawing, self.xValue, self.yValue)

    def move(self):
        self.xValue -= 3

# image taken from:
# http://www.pixeljoint.com/files/icons/full/fireballz.gif
class MarioFireball(object):
    def __init__(self, canvas, lane, marioX, staffTop, staffHeight):
        self.canvas = canvas
        self.lane = lane
        self.xValue = marioX
        self.staffTop = staffTop
        self.staffHeight = staffHeight
        self.image = PhotoImage(file="images/marioFireball.gif")
        self.setYValue()

    def setYValue(self):
        numLanes = 8 # number of lanes in staff
        spacing = self.staffHeight / numLanes
        self.yValue = self.staffTop + self.staffHeight - (self.lane * spacing)

    def draw(self):
        self.drawing = self.canvas.create_image(self.xValue, self.yValue,
            image = self.image)

    def updateDrawing(self):
        self.canvas.coords(self.drawing, self.xValue, self.yValue)

    def move(self):
        self.xValue += 15

Game().run()