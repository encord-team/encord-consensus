# Consensus Tool Overview

## Overview
In this tool, we assume that we have a dataset and an ontology set up on the platform.
Then, a number of projects referencing the same dataset and ontology are set up.
It is understood that each annotator is assigned to a specific project, which will hold the annotator's annotations.

In this tool, we can select an arbitrary number of such projects, which will be compared in order to understand consensus and identify regions of interest, where 'true' classifications may exist.
We consider two classifications to be 'equal' if they contain the same answers.
Note that these answers must be equal all the way down the nested hierarchy.
If a single answer differs, the classifications are not equal.

Regions of interest are labelled according to the following format
```
question1=answer1&question2=answer2...&questionN=answerN@region_of_interest_M
```
where you can see that the `questionI=answerI` structure repeats for as many answers as there are in the classification, separated by `&`.
The `@region_of_interest_M` is used to identify the region of interest, since there may be multiple across a video.

Regions of interest are identified by looking for gaps in annotation.
If 2 people label 0-10 as `is_walking=yes` and 3 people label 15-20 as `is_walking=yes`, then we will generate two regions of interest:
one for `0-10` and one for `15-20`.
These are not considered the same region as there is a gap between them (no annotator indicated that 11-14 could be `is_walking=yes`).

## Setup
1. Create a directory to hold the environment
```commandline
mkdir some-dir-name
cd some-dir-name
```
2. Set up your python environment (this only has to be done once):
```commandline
python3.11 -m venv env
source env/bin/activate
```
For Windows environments, the command to activate the environment is
```commandline
.\env\Scripts\activate
```
3. Create a `.env`  file and specify the path to your private keyfile (this only has to be done once):
```commandline
echo "ENCORD_KEYFILE=/path/to/keyfile/.ssh/id_ed25519" > .env
```
On Windows it may be necessary to open the file in Notepad and save it as utf-8 without BOM.
File>Save As, then change 'Save as type' to 'All files' and choose 'Encoding' as `UTF-8`.
This only has to be done once.

4. Install the tool:
```commandline
pip install git+ssh://git@github.com/encord-team/encord-consensus.git
```

## GUI
### Starting the app
1. Before starting the app, you will need to activate your virtual environment.
2. Run `encord-consensus` in your terminal.
This will bring up the app in your browser, which you can use to run consensus.

### Using the app
When the app loads, you can search for projects by name.
Note that whilst this is a fuzzy search (you can enter parts of a project name and it will search for them), it is sensitive to capitalisation.
Select the projects you want to add to the consensus comparison.
You can only select projects with the same datasets and ontologies.
Additionally, we run some checks to see if the tasks within the projects have been labelled at least once.

Once you have selected all the required projects, select the relevant data item to run consensus on.
Depending on the number of labels, length of video and number of projects being targeted this may take some time.

You will then see a global consensus report, showing on how many frames a minimum of N annotators agreed.
The maximum agreement is the number of projects (implicitly annotators) being compared.

You will have access to 2 sliders, which allow you to filter by two parameters:
1. Minimum Agreement
2. Score

When you apply these filters, you will see regions of interest, which are automatically identified by the tool.

If you want to select new projects or data rows, the easiest thing to do is to refresh the browser page or press `ctrl-c` in the terminal to kill the app and then run `streamlit run app.py` to restart the app.

#### Minimum Agreement
The minimum agreement will show regions of interest where a minimum of N labellers applied a classification.
If you set this to 3, and only 2 labellers labelled a region for a specific classification and corresponding answers (e.g. Lesion->Yes), then this will be filtered out and not shown.
If however, a third labeller also applied this classification, the region will be shown.

It is important to note that this does not mean that you will only see the region for which all N annotators have agreed.
You will see the entire region of interest, but there will have to be a place where at least N annotators agreed at any one point.
This agreement does not have to span the whole region of interest.

#### Score
For a given region of interest, there will be a certain number of 'points' available.
This number of available points is the number of frames that the region of interest spans multiplied by the total possible number of annotators (i.e. the numnber of projects being compared).
The number of points achieved is the sum of all the frames which each annotator who labelled this region of interest submitted.

The score is `number_of_points_achieved / number_of_points_available`

For example, if consensus is being run on 4 projects and there is a region of interest spanning 10 frames, the maximum number of points available is `4 x 10 = 40`.
If 1 annotator labelled frames 1-10, this counts as 10 points achieved. The score would be `10 / 40 = 0.25` for this region.
If another annotator labelled frames 1-5, then this would add another 5 points. The total score would be `(10 + 5) / 40 = 0.375` for this region.

If all 4 annotators had labelled 1-10 in this region, then the score would be `(10 x 4) / 40 = 1`, which is the maximum possible score.
This makes sense as a score of 1 implies perfect agreement.

## Export
We are adding support for exporting the new accepted consensus based labels to the Encord JSON format.
This will be an export of accepted regions of interest as a new label.

## CLI
Support for this is coming soon.
