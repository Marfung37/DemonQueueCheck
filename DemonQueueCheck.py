from csv import reader
import re
import subprocess
import os

SEESEVEN = 7
queue = "OIZJTSTILJ"
bagSeparatorIndex = 6
baseFumen = "v115@ahglGeilJeAgH" # starting board

def getHighestPercentPlacements(pieceToTry, piecesForPercent, fumen):
    highestPlacements = []

    # get placements
    subprocess.call(f"java -jar sfinder.jar move  -t '{fumen}' -p '{pieceToTry}'".split(), stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)
    print(piecesForPercent)

    currHighestChance = 0
    with open(os.path.join("output", "move.csv"), "r") as outfile:
        csvReader = reader(outfile)
        for line in csvReader:
            fumenWithNewPlacement = line[1]

            subprocess.call(f"java -jar sfinder.jar percent -t '{fumenWithNewPlacement}' -p '{piecesForPercent}' -d 180 -fc 0".split(), stdout=open(os.devnull, "w"), stderr=subprocess.STDOUT)

            with open("output/last_output.txt", "r") as percentOut:
                percentLine = percentOut.readlines()[28]

                percentMatchObj = re.match("success = \d+\.\d\d% \((\d+)/(\d+)\)", percentLine)
                
                if percentMatchObj is None:
                    raise "Didn't find percent line in last_output.txt"

                # get value from fraction to higher percision
                numerator, denominator = map(int, percentMatchObj.groups())

                chance = numerator / denominator

                # found a chance higher
                if chance > currHighestChance:
                    highestPlacements = [fumenWithNewPlacement]
                    currHighestChance = chance
                elif chance == currHighestChance:
                    highestPlacements.append(fumenWithNewPlacement)
    
    return highestPlacements, currHighestChance

def determineSfinderPieces(piece, queue, queueBagSeparatorIndex):
    # assume see 7

    # get the piece index
    pieceIndex = queue.index(piece)

    # if can see the entire next bag then return the queue removed the piece
    if len(queue) <= SEESEVEN:
        return queue[: pieceIndex] + queue[pieceIndex + 1:]

    # otherwise generate the pieces before next bag part
    firstBagKnownPieces = queue[: pieceIndex] + queue[pieceIndex + 1: queueBagSeparatorIndex]

    # next bag known pieces
    nextBagKnownPieces = queue[queueBagSeparatorIndex: SEESEVEN]

    if nextBagKnownPieces:
        possiblePiecesInUnknownNextBag = f"[^{nextBagKnownPieces}]"
    else:
        possiblePiecesInUnknownNextBag = "*"

    # determine length of the part not seen
    if SEESEVEN > bagSeparatorIndex:
        nextBagLength = len(queue) - SEESEVEN
    else:
        nextBagLength = len(queue[bagSeparatorIndex: ])

    # return the sfinder pieces with bag
    return f'{firstBagKnownPieces}{nextBagKnownPieces},{possiblePiecesInUnknownNextBag}p{nextBagLength}'

def demonQueueCheck(queue, baseFumen, bagSeparatorIndex, chance=-1, depth=0):
    # assume hold
    if chance != -1:
        bestTree = [baseFumen, f"{chance * 100:.2f}%", []]
    else:
        bestTree = [baseFumen, "", []]
    piece1 = queue[0]
    piece2 = queue[1]

    somethingWorking = False
    
    highestPercentFumens, piece1Chance = getHighestPercentPlacements(piece1, determineSfinderPieces(piece1, queue, bagSeparatorIndex), baseFumen)
    if 0 < piece1Chance:
        # get the piece out of queue
        piece1NextQueue = queue[1:]
        if len(queue) < SEESEVEN + 1:
            somethingWorking = piece1Chance == 1
        else:
            anyWorking = False
            allWorking = 0
            for fumen in highestPercentFumens:
                worked, subTree = demonQueueCheck(piece1NextQueue, fumen, bagSeparatorIndex - 1, chance=piece1Chance, depth=depth + 1)
                anyWorking = anyWorking | worked
                if worked:
                    allWorking += 1
                    bestTree[2].append(subTree)
            
            if piece1Chance:
                somethingWorking = len(highestPercentFumens) == allWorking
            else:
                somethingWorking = somethingWorking | anyWorking
    
    highestPercentFumens, piece2Chance = getHighestPercentPlacements(piece2, determineSfinderPieces(piece2, queue, bagSeparatorIndex), baseFumen)
    if piece2Chance >= piece1Chance:
        if piece2Chance > 0:
            # get the piece out of queue
            piece2NextQueue = queue[0] + queue[2:]
            if len(queue) < SEESEVEN + 1:
                somethingWorking = piece1Chance == 1
            else:
                anyWorking = False
                allWorking = 0
                for fumen in highestPercentFumens:
                    worked, subTree = demonQueueCheck(piece2NextQueue, fumen, bagSeparatorIndex - 1, chance=piece2Chance, depth=depth + 1)
                    anyWorking = anyWorking | worked
                    if worked:
                        allWorking += 1
                        bestTree[2].append(subTree)
                
                if piece2Chance != 1:
                    somethingWorking = len(highestPercentFumens) == allWorking
                else:
                    somethingWorking = somethingWorking | anyWorking

    return somethingWorking, bestTree

def outputTree(subTree, outputFile, currFumenSeq=(), depth=0):
    for branch in subTree:
        fumen, chance, nextSubTree = branch
        if chance:
            commentP = subprocess.Popen(["node", "addCommentToFumen.js", fumen, str(chance)], stdout=subprocess.PIPE)
            fumen = commentP.stdout.read().decode().rstrip()
        
        if nextSubTree:
            outputTree(nextSubTree, outputFile, currFumenSeq + (fumen,), depth + 1)
        else:
            combineP = subprocess.Popen(f"node combineFumens.js {' '.join(currFumenSeq + (fumen,))}".split(), stdout=subprocess.PIPE)
            combinedFumen = combineP.stdout.read().decode()
            outputFile.write(combinedFumen)

if __name__ == "__main__":
    outputFile = open("outputWorkingFumens.txt", "w")

    worked, bestTree = demonQueueCheck(queue, baseFumen, bagSeparatorIndex)
    print(worked)
    if worked:
        outputTree([bestTree], outputFile)


    
