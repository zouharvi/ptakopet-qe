import os
from utils import DirCrawler, bash

import sys
sys.path.append("..") # Adds higher directory to python modules path.
from align import fast_align

"""
QuestPlusPlus driver
"""
class QuestPlusPlus():
    supportedPairs = [['en','cs']]
    def qe(self, sourceLang, targetLang, sourceText, targetText):
        """
        @TODO: documentation
        It's ok to raise Exceptions here. They are handled upstream.
        """
        os.makedirs('data/tmp', exist_ok=True)

        if not [sourceLang, targetLang] in self.supportedPairs:
            raise Exception("{}-{} language pair not supported".format(sourceLang, targetLang))

        alignments = fast_align.FastAlign().align(sourceLang, targetLang, sourceText, targetText)['alignment']
        with open('data/tmp/alignments', 'w') as fileAlignments:
            fileAlignments.write(alignments)

        with open('data/tmp/source', 'w') as fileSource:
            fileSource.write(sourceText)

        with open('data/tmp/target', 'w') as fileTarget:
            fileTarget.write(targetText)


        with DirCrawler('qe/questplusplus'):
            print("Extracting features")
            (output, error) = bash("""
                 java -cp QuEst++.jar:lib/* shef.mt.WordLevelFeatureExtractor
                 -lang english spanish
                 -input ../../data/tmp/source ../../data/tmp/target
                 -alignments ../../data/tmp/alignments
                 -config ../questplusplus-config/config.word-level.properties
                 """)

            outputFile = 'output/test/output.txt'
            if not os.path.isfile(outputFile):
                raise Exception('Server Processing Error')
            with open(outputFile, 'r') as outputFileR:
                features = outputFileR.readlines()

        os.remove('data/tmp/alignments')
        os.remove('data/tmp/source')
        os.remove('data/tmp/target')

        features = [[x.split('=')[1] for x in line.rstrip('\n').rstrip('\t').split('\t')] for line in features]
        with open('data/tmp/features', 'w') as fileFeatures:
            fileFeatures.write('\n'.join(['\t'.join(x) for x in features]))
        with open('data/tmp/labels', 'w') as fileLabels:
            fileLabels.write('\n'.join(['1']*len(features)))

        with DirCrawler('qe/questplusplus'):
            print("Removing output directory structure for feature extractor")
            os.remove(outputFile)
            os.rmdir('output/test')
            os.rmdir('output')

            print("Machine Learning")
            (output, error) = bash("""
                python learning/src/learn_model.py ../questplusplus-config/svr.cfg
                """)
                
            with open('predicted.csv', 'r') as predictedFile:
                output = [float(x.rstrip('\n').split('\t')[1]) for x in predictedFile.readlines()]
            os.remove('predicted.csv')

        os.remove('data/tmp/features')
        os.remove('data/tmp/labels')
        os.rmdir('data/tmp')
        return {'status': 'OK', 'qe': output }