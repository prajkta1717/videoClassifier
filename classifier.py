import re
from collections import defaultdict
import MySQLdb
from flask import render_template, request
from flask import Flask
from nltk.corpus import stopwords


stop_words = set(stopwords.words('english'))

from collections import Counter

app = Flask(__name__)

@app.route('/')
def hello_world():
   return render_template('classification.html')


@app.route('/classification',methods = ['POST', 'GET'])
def classification():
    if request.method == 'POST':

        fullTextToBeSearched = request.form.get("textSearch").lower()
        db = MySQLdb.connect("localhost", "root", "root123", "test")
        freqOfClass = "select category_id,title,count(*) AS classFrequency from cavideos group by category_id;"
        with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute(freqOfClass)
            allCategInfo = cursor.fetchall()

        allData = "SELECT video_id,channel_title,category_id,title,likes,dislikes,views,description,thumbnail_link FROM cavideos"
        with db.cursor(MySQLdb.cursors.DictCursor) as cursor:
            cursor.execute(allData)
            allDataResult = cursor.fetchall()

        arrDictOfProbabilityClass = []
        arrDictOfWordsCountOfClass = []

        for video in allCategInfo:
            dictClassProbability = {}
            dictClassWordsCount = {}
            counter = 0
            dictClassProbability.update(categoryId=video.get('category_id'),
                                        classProbability=video.get('classFrequency') / len(allDataResult))
            arrDictOfProbabilityClass.append(dictClassProbability)
            for data in allDataResult:
                if (video.get('category_id') == data.get('category_id')):
                    temp = video.get('title').split(' ')
                    counter = counter + len(temp)
            dictClassWordsCount.update(category_id=video.get('category_id'), countOfwords=counter)
            arrDictOfWordsCountOfClass.append(dictClassWordsCount)

        def CountFrequency(my_list):
            freq = {}
            for item in my_list:
                if (item in freq):
                    freq[item] += 1
                else:
                    freq[item] = 1
            return freq

        arrWordList = []
        finalListwithCatId = {}
        index = 0
        for videodata in allDataResult:
            for word in videodata.get("title").split():
                word = re.sub("[^\w\s]", " ", word)
                if word not in stop_words:
                    dictWordCategoryInfo = {}
                    dictWordCategoryInfo[word] = videodata.get("category_id")
                    arrWordList.append(dictWordCategoryInfo)

        mergedWordCategDict = defaultdict(list)
        finalMergedWordCategDict = {}

        for d in arrWordList:  # you can list as many input dicts as you want here
            for key, value in d.items():
                mergedWordCategDict[key].append(value)

        for k, v in mergedWordCategDict.items():
            if not (k == ' '):
                wordFreqCount = CountFrequency(v)
                finalMergedWordCategDict[k] = wordFreqCount
        countOfUniqueWords = len(finalMergedWordCategDict)

        tempdict = {}
        dictProbabilityResult = {}
        probabilityOfSearchedText = {}
        arrFullTextToBeSearched = fullTextToBeSearched.lower().split(' ')
        for i in arrFullTextToBeSearched:

            try:

                for textWord in finalMergedWordCategDict:
                    if (textWord.lower() == i):
                        tempdict = finalMergedWordCategDict.get(textWord)

                for category in [o['category_id'] for o in allCategInfo]:

                    for categoryWordCount in arrDictOfWordsCountOfClass:
                        tempWordCount = 0
                        if (categoryWordCount.get('category_id') == category):
                            tempWordCount = categoryWordCount.get('countOfwords')
                            if not (category in tempdict.keys()):
                                categoryFrequency = 0
                            else:
                                categoryFrequency = tempdict.get(category)
                    probabilityForCAtegory = (categoryFrequency + 1) / (tempWordCount + countOfUniqueWords)
                    categoryProbabilityDict = {category: probabilityForCAtegory}
                    dictProbabilityResult.update(categoryProbabilityDict)
                    probabilityOfSearchedText[i] = dictProbabilityResult
            except:

                return render_template("error.html")
                print("fail")
        print("probabilityOfSearchedText")
        print(probabilityOfSearchedText)

        productOfProbOfSearchedText = {1: 1, 2: 1, 10: 1, 15: 1, 17: 1, 19: 1, 20: 1, 22: 1, 23: 1, 24: 1, 25: 1, 26: 1,
                                       27: 1, 28: 1, 29: 1, 30: 1, 43: 1}
        classNames = {1: "Film & Animation", 2: "Autos & Vehicles", 10: "Music", 15: "Pets & Animals", 17: "Sports",
                                       19: "Travel & Events", 20: "Gaming", 22: "People & Blogs", 23: "Comedy", 24: "Entertainment", 25: "News & Politics",
                                       26: "Howto & Style", 27: "Education", 28: "Science & Technology", 30: "Movies", 43: "Shows"}

        for searchedText in probabilityOfSearchedText:
            for category in allCategInfo:
                temp = (productOfProbOfSearchedText[category.get('category_id')]) * (
                    probabilityOfSearchedText.get(searchedText).get(category.get('category_id')))
                productOfProbOfSearchedText[category.get('category_id')] = temp

        dictProbabilityTochooseCategory = {}
        for category in allCategInfo:
            for probOfClass in arrDictOfProbabilityClass:

                if (category.get('category_id') == probOfClass.get('categoryId')):
                    probabilityTochooseCategory = probOfClass.get('classProbability') * productOfProbOfSearchedText.get(
                        category.get('category_id'))
                    dictProbabilityTochooseCategory[probOfClass.get('categoryId')] = probabilityTochooseCategory

        result = {}
        resultPercentDict = {}
        topThreeResult = {}

        for key, value in sorted(dictProbabilityTochooseCategory.items(), key=lambda kv: kv[1], reverse=True):
            result[key] = value

        c = Counter(result)
        for x in list(result)[0:3]:
            topThreeResult[x]= result[x]

        Sum = sum(topThreeResult.values())
        for ky,val in topThreeResult.items():
            pct = val * 100.0 / Sum
            resultPercentDict[classNames[ky]] = pct

        return render_template("classificationResult.html", classificationResult=resultPercentDict)



if __name__ == '__main__':
    app.run()