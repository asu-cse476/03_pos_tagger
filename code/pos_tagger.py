import argparse
import collections
import math
import operator
import random

import utils


def create_model(sentences):
    ## Data structures to store the model.
    ## You can modify this data structures if you want to
    prior_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    priors = collections.defaultdict(lambda: collections.defaultdict(float))
    likelihood_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    likelihoods = collections.defaultdict(lambda: collections.defaultdict(float))

    majority_tag_counts = collections.defaultdict(lambda: collections.defaultdict(int))
    majority_baseline = collections.defaultdict(lambda: "NN")

    tag_counts = collections.defaultdict(int)

    #x = utils.read_tokens(sentences, max_sents=-1, test=False)
    count = 0
    
    for n in sentences:
        for i in n:
            majority_tag_counts[i.word, i.tag] = majority_tag_counts.get((i.word, i.tag), 0) + 1 
            #count of what a word is tagged as: (word, tag): number

            tag_counts[i.tag] = tag_counts.get(i.tag, 0) + 1
            #total count of each type of tag
            
    
            if count == 0:
                pass
            else:
                prior_counts[prev.tag, i.tag] = prior_counts.get((prev.tag, i.tag), 0)+1
                #count of tag followed by another tag: (tag, tag-1): number
            prev = i
            count+=1

    sorted_tuples = sorted(majority_tag_counts.items(), key=operator.itemgetter(1), reverse = True)
    majority_tag_counts = {k: v for k, v in sorted_tuples}
    #gets the word and its tag count in ascending order
    for n in majority_tag_counts:
        if n[0] not in majority_baseline:
            majority_baseline[n[0]] = n[1]
            #puts the main tag with the word: {word: main tag}
    for n in sentences:
        for i in n:
            value = majority_tag_counts.get((i.word,i.tag), 0)/(tag_counts.get(i.tag,0))
            likelihoods[i.word, i.tag] = value
            #probability of word being tagged as something: {(word, tag): probability}

    counter = False
    for n in sentences:
        for i in n:
            if counter == False:
                pass
            else:
                value = (prior_counts.get((prev.tag, i.tag), 0)+1)/(tag_counts.get(i.tag,0)+len(tag_counts))
                priors[prev.tag, i.tag] = value
            prev = i
            counter = True
    #probability a tag follows another tag {(tag, tag): probability}

    


    ## You can modify the return value if you want to
    return priors, likelihoods, majority_baseline, tag_counts


def predict_tags(sentences, model, mode='always_NN'):
    priors, likelihoods, majority_baseline, tag_counts = model

    viterbi = {}
    pushinP={}
    bestPathProb={}
    bestPathPointer={}
    bestPath={}
    for sentence in sentences:
        if mode == 'always_NN':
            # Do NOT change this one... it is a baseline
            for token in sentence:
                token.tag = "NN"
        elif mode == 'majority':
            # Do NOT change this one... it is a (smarter) baseline
            for token in sentence:
                token.tag = majority_baseline[token.word]
        elif mode == 'hmm':
            # TODO The bulk of your code goes here
            #   1. Create the Viterbi Matrix
            #   2. Fill the Viterbi matrix
            #      You will need one loop to fill the first column
            #      and a triple nested loop to fill the remaining columns
            #   3. Recover the sequence of tags and update token.tag accordingly
            # The current implementation tags everything as an NN you need to change it
            sentence[1].tag = "<s>"
            for i in tag_counts:
                viterbi[(i, 1)] = priors.get(("<s>", i), 1/(tag_counts["<s>"] + len(tag_counts))) * likelihoods.get((sentence[1].word, i), 0)
                pushinP[(i, 1)] = 0
            for t in range(2, len(sentence)):
                #token.tag = "NN"
                if sentence[t].word == "</s>":
                    sentence[t].tag = "</s>"

                hasSeen = False
                for s in tag_counts:
                    counter = 0
                    bestTag = "NNP"
                    if(not likelihoods.get((sentence[t].word, s), 0) == 0):
                        hasSeen = True
                    randoms = []
                    for prevS in tag_counts:
                        current = viterbi[(prevS, t-1)] * priors.get((prevS, s), 1/(tag_counts[prevS] + len(tag_counts)))
                        if current > counter:
                            counter = current
                            bestTag = prevS
                        '''elif current == counter:
                            randoms.append(prevS)
                            bestTag = random.choice(tuple(randoms))
                            counter = current'''
                    viterbi[(s, t)] = counter * likelihoods.get((sentence[t].word, s), 0)
                    pushinP[(s, t)] = bestTag

                if not hasSeen:
                    #print(sentence[t].word)
                    if sentence[t].word[0].isupper() and sentence[t-1].word != '<s>':
                        viterbi[('NNP',t)] = 1
                    elif sentence[t].word[-2:] =='ed':
                        viterbi[('VBD',t)] = 1 
                        viterbi[('VBN', t)] = 1
                    elif sentence[t].word[-2:] =='es':
                        viterbi[('VBZ',t)] = 1
                    elif sentence[t].word[-3:] =='ing':
                        viterbi[('VBG',t)]=1
                    elif sentence[t].word[0].isdigit() and sentence[t].word[-1].isdigit():
                        viterbi[('CD', t)] = 1
                    elif sentence[t].word[-2:] == 'ly':
                        viterbi[('RB', t)]=1
                    else:
                        viterbi[('RB', t)] = 1
                        viterbi[('NN',t)]=1

                    # else:
                        

            counter = -99999
            bestTag = "NNP"
            
            for s in tag_counts:
                if viterbi.get((s, len(sentence)-2),0) > counter:
                    counter = viterbi.get((s, len(sentence)-2), 0)
                    bestTag = s

            sentence[len(sentence)-2].tag = bestTag
                # if viterbi.get((s, len(sentence)),0) > otherCount:
                #     otherCount = viterbi.get((s, len(sentence)),0)
                #     bestPathPointer = otherCount

            for t in reversed(range(2, len(sentence)-2)):
                sentence[t].tag = pushinP[(sentence[t+1].tag, t+1)]

        else:
            assert False

    

    return sentences

if __name__ == "__main__":
    # Do NOT change this code (the main method)
    parser = argparse.ArgumentParser()
    parser.add_argument("PATH_TR",
                        help="Path to train file with POS annotations")
    parser.add_argument("PATH_TE",
                        help="Path to test file (POS tags only used for evaluation)")
    parser.add_argument("--mode", choices=['always_NN', 'majority', 'hmm'], default='always_NN')
    args = parser.parse_args()

    tr_sents = utils.read_tokens(args.PATH_TR) #, max_sents=1)
    # test=True ensures that you do not have access to the gold tags (and inadvertently use them)
    te_sents = utils.read_tokens(args.PATH_TE, test=True) #changed to 10

    model = create_model(tr_sents)

    print("** Testing the model with the training instances (boring, this is just a sanity check)")
    gold_sents = utils.read_tokens(args.PATH_TR)
    #predictions = predict_tags(utils.read_tokens(args.PATH_TR, test=True), model, mode=args.mode)
    #accuracy = utils.calc_accuracy(gold_sents, predictions)
    #print(f"[{args.mode:11}] Accuracy "
    #      f"[{len(list(gold_sents))} sentences]: {accuracy:6.2f} [not that useful, mostly a sanity check]")
    print()

    print("** Testing the model with the test instances (interesting, these are the numbres that matter)")
    # read sentences again because predict_tags(...) rewrites the tags
    gold_sents = utils.read_tokens(args.PATH_TE)#changed to 10
    predictions = predict_tags(te_sents, model, mode=args.mode)
    accuracy = utils.calc_accuracy(gold_sents, predictions)
    print(f"[{args.mode}:11] Accuracy "
          f"[{len(list(gold_sents))} sentences]: {accuracy:6.2f}")
