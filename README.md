# Interactive Social Task Learning
(from *Interactive Task Learning for Social Robots: a Pilot Study* in IEEE IROS 2023)

## Code structure
**FurhatDriver** contains the client skill that must be run on the furhat robot. 
This skill is also responseible for hosting the website. 
Compile and run per the Furhat Skill developer docs: (https://docs.furhat.io/skills/)

**social_itl** contains the server code that performs all of the interaction logic.
To setup:
1. Install dependencies from requirements.txt
2. Run `dataset.py` to generate the synthetic dataset
3. Run `train_anonymizer.py` to train the masking BERT model
4. Run `train_parser.py to train the parsing model`
5. Run `sentence_classifier.py` to train the sentence classifier

To run the full system, start the furhat driver and run `python -m social_itl --host <ip address>` with the IP address of the furhat robot.
