# TwitterBot

TwitterBot: An utility to like tweets using Hashtags. 

## Specifications:

##### TwitterBot has 2 Python files.

### app.py

It has two functions:

1. Login ( `login(self)` ): It accepts `self` as parameter. 

2. Like Tweet ( `like_tweet(self,hashtag)` ): It accepts `self` and `hashtag` as parameter. `hashtag` can be anything e.g. 'machinelearning','python',etc.

### twitter.py

It's unit test file to test whether login is working with your mozilla firefox browser. TwitterBot uses Gecko driver. Gecko driver acts as a link between Selenium Web Driver tests and Mozilla Firefox browser.

## Usage

1. Pull/Download this package to your system. 
2. Download Gecko driver https://github.com/mozilla/geckodriver/releases
3. Place it inside root of Python folder.
4. Change directory (CD)/ switch to your root folder e.g. TwitterBot.
4. From your console type below command.
```python
python app.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)