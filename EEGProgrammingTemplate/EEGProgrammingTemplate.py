from psychopy import gui, os, data, visual, core, event, parallel
import pandas

##Settings##
settings = pandas.read_excel('settings.xlsx') #Change the parameters in 'settings.xlsx' upon your preferences
NrOfTrialsPerBlock = settings.iloc[0,0] #Change this upon your preferences. Can only be perfect multiplication of the nr of conditions in your Excel file 'stimuli.xlsx'
NrOfBlocksMainExperiment = settings.iloc[0,1]
ValuePerRewardTrial = settings.iloc[0,2] #How much can participants earn per reward trials (in euros)

EEGLab = settings.iloc[0,3] #'ActiChamp'/'BioSemi'/None
QuickPilotMode = settings.iloc[0,4] #True/False. True if you want to run all trials all breakneck speed

##File management & dialog box##
DirectoryToWriteTo = os.getcwd() + '/MyExpData/' #Create data folder (if this does not yet exist). os.getcwd() is where your script is saved
if not os.path.isdir(DirectoryToWriteTo):
    os.mkdir(DirectoryToWriteTo)

info = {'ParticipantNr': 0, 'age': 0, 'gender' : ['male','female','x']} #Dictionary for dlg box. I collect all data here that is typically needed for a method section in a paper

AlreadyExists = True
while AlreadyExists:
    dlg = gui.DlgFromDict(dictionary = info, title = 'MyExp') #Present a dlg box
    if not dlg.OK: #Quit the experiment if 'Cancel' is selected
        core.quit()
    if not os.path.isfile(DirectoryToWriteTo + 'DataOfParticipant_' + str(info['ParticipantNr']) + '.csv'): #Only escape the while loop if ParticipantNr is unique
        AlreadyExists = False
    else:
        dlg2 = gui.Dlg(title = 'Error') #If the ParticipantNr is not unique, present an error msg
        dlg2.addText('This ParticipantNr is in use already, please select another')
        dlg2.show() #For this dlg method we need the .show() for presenting

ThisExp = data.ExperimentHandler(dataFileName = DirectoryToWriteTo + 'DataOfParticipant_' + str(info['ParticipantNr']), extraInfo = info) #ExperimentHandler: a class for keeping track of multiple loops/handlers

##EEG admin##
if EEGLab == 'ActiChamp':
    parallel.setPortAddress('0xCFB8')
elif EEGLab == 'BioSemi':
    parallel.setPortAddress('0xCFE8')

def SendEEGTrigger(EEGTrigger):
    if EEGLab == 'ActiChamp' or EEGLab == 'BioSemi':
        parallel.setData(EEGTrigger)
        core.wait(0.01)
        parallel.setData(0)

##Read in the conditions from Excel##
TrialList = data.importConditions('stimuli.xlsx') #Change the parameters in 'stimuli.xlsx' upon your preferences

##Read in the participant instructions from Excel##
ParticipantInstructions = pandas.read_excel('ParticipantInstructions.xlsx') #Change the instructions in 'ParticipantInstructions.xlsx' upon your preferences

##Initialize clock, response, window, and stimuli properties##
RTClock = core.Clock() #Initialize the clock
ResponseButtons = ['f','j'] #Give in the response keys here
ResponseButtons.append('escape') #Just to make sure that you can escape the experiment (of note, 'escape' is tracked only at the moment that you register the response to the target)

win = visual.Window(fullscr = True, units = 'norm')
Instructions = visual.TextStim(win, text = '', height = .05)
TextStimulus = visual.TextStim(win, text = '')

##Experiment presentation##
for ExpPhase in ['practice','main']:
    
    if ExpPhase == 'practice': #This admin step is needed for the block loop below
        NrOfBlocks = 1 #One practice block
    else:
        NrOfBlocks = NrOfBlocksMainExperiment #Multiple blocks for main experiment (as defined by you in settings.xlsx)
    
    for BlockNr in range(NrOfBlocks):
        
        if ExpPhase == 'practice':
            Instructions.text = ParticipantInstructions.iloc[0,0].replace('.', '.\n\n') #PracticeInstructions. The replace is for the readability of the instructions (add white line after each '.')
            trials = data.TrialHandler(TrialList, nReps = 1, method = 'random') #One time all trials within the one practice block
        else:
            if BlockNr == 0:
                Instructions.text = ParticipantInstructions.iloc[0,1].replace('.', '.\n\n') #MainTaskInstructions
                MainExpTrialCounter = 0 #These three variables are needed for the block feedback that updates the participant on the %-correct and the amount of money earned so far
                CorrectCounter = 0
                MoneyEarned = 0
            else:
                Instructions.text = ParticipantInstructions.iloc[0,2].replace('.', '.\n\n') #BreakInstructions
            trials = data.TrialHandler(TrialList, nReps = (NrOfTrialsPerBlock/len(TrialList)), method = 'random') #Takes the nr of trials from the settings that you defined earlier

        ThisExp.addLoop(trials) #Here we connect the TrialHandler to the ExperimentHandler

        Instructions.draw()
        win.flip()
        event.waitKeys(keyList = ['space'])
        
        for trial in trials:
            
            #Cue presentation
            TextStimulus.text = trial['CueValence']
            TextStimulus.color = 'white'
            TextStimulus.draw()
            win.flip()
            SendEEGTrigger(trial['CueEEGMarker'])
            if not QuickPilotMode:
                core.wait(trial['CueDuration'])
                
                win.flip() #To empty the screen
                core.wait(trial['CueTargetInterval'])
            
            #Target presentation
            TextStimulus.text = trial['TargetNr']
            TextStimulus.color = trial['TargetColor']
            TextStimulus.draw()
            win.flip()
            SendEEGTrigger(trial['TargetEEGMarker'])
        
            #Response registration
            RT = RTClock.reset()
            accuracy = '' #needed for QuickPilotMode
            if not QuickPilotMode:
                keys = event.waitKeys(keyList = ResponseButtons, maxWait = trial['TargetDuration'])
                if keys:
                    RT = round(RTClock.getTime() * 1000) #In ms
                    if keys[0] == 'escape': #To escape the practice/main experiment by pressing 'escape'(only works at the moment that you register the response to the target)
                        break
                    response = keys[0]
                    accuracy = ['error','correct'][((keys[0] == trial['TargetCorrectResponse'])*1)]
                else:
                    RT = -999
                    response = 'miss'
                    accuracy = 'TooLate'
                
                ResponseEEGMarker = [75,100,125][['correct','error','TooLate'].index(accuracy)]
                SendEEGTrigger(ResponseEEGMarker) #75 for correct, 100 for error, 125 for Toolate, you can simply adjust this in the line above this one
                trials.addData('ResponseEEGMarker', ResponseEEGMarker) #These are not automatically in your data file because these werent't imported via data.importConditions('stimuli.xlsx')

                if RTClock.getTime() < trial['TargetDuration']: #So that targets have the same duration in each trial (it would otherwise disappear after the response has been registered)
                    core.wait((trial['TargetDuration'] - RTClock.getTime()))
                trials.addData('ExpPhase', ExpPhase) #This is all data file admin
                trials.addData('Response', response)
                trials.addData('accuracy', accuracy)
                trials.addData('RT', RT)

            if ExpPhase == 'main':
                MainExpTrialCounter += 1 #Needed for the calculation of the block feedback
                if accuracy == 'correct':
                    CorrectCounter += 1
                    if trial['CueValence'] == '€':
                        MoneyEarned += ValuePerRewardTrial
                trials.addData('PercentageCorrect', (CorrectCounter/MainExpTrialCounter))
                trials.addData('MoneyEarned', MoneyEarned)

            ThisExp.nextEntry()
            
            if not QuickPilotMode:
                win.flip() #To empty the screen
                core.wait(trial['TargetCueInterval'])
        
        if not QuickPilotMode:
            if keys:
                if keys[0] == 'escape':
                    break
        
        if ExpPhase == 'main': #As variables are incorporated in this text (euro and %-correct), you cannot simply define this text in an Excel file
            Instructions.text = 'During the main experiment, you responded correct and in-time to {0:.0%} of the trials\n\nYou earned {1:.2f} euros.\n\nPress SPACE to continue.'.format((CorrectCounter/MainExpTrialCounter), MoneyEarned)
            Instructions.draw()
            win.flip()
            event.waitKeys(keyList = ['space'])

Instructions.text = ParticipantInstructions.iloc[0,3].replace('.', '.\n\n') #ThankYouInstructions
Instructions.draw()
win.flip()
keys = event.waitKeys(keyList = ['space'])