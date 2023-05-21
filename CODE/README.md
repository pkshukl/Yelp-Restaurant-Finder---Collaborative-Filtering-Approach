# Restaurant Finder

This application is a restaurant search and recommendation application. It uses publicly available Yelp data to help users find restaurants they will enjoy, both through search parameters and through recommendations based on user similarity.

The application uses Python, Flask, and sqlite as it's backend, while using HTML/CSS/Javascript for it's frontend.

## Setup

Install Docker: 

https://www.docker.com/products/docker-desktop/

### Launch Docker Dev Environment using vscode
IDE Install vscode: https://code.visualstudio.com/download
Docker Extension: https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker
Container Extension: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers 

Using vscode, Ctrl+Shift+P and search for Dev Containers: Reopen in Container
Vscode will setup the container and relaunch within the container, allowing you to develop with the same environment 
the application was developed in. The process will automatically install all necessary dependencies.
Be sure to always open the project within the container.

### Launch Docker Dev Environment using other IDEs
I recommend vscode because of of it's built in container extension which makes this easy, but other IDEs are possible. I only recommend going with other IDEs if you have some experience using Docker already.
Pycharm: https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html

### Downloading the dataset and placing it in the correct location in the project

Download the yelp dataset by navigating to: https://www.yelp.com/dataset/download
You will need to enter your name, email, and agree to terms of use.
Then you will be taken to a download page.
Make sure to download both the json data and the photos data.
Create a folder within the project called "yelp_data" and decompress the contents of the json download there
Create a folder within the project called "photos" and decompress the contents of the photos download there
The final structure should look like this:
```
root@02c7efc22e05:/workspaces/team-88-project-dva-2023/yelp_data# ls -l
total 9108572
-rw-r--r-- 1 1000 1000      80358 Feb 15  2022 Dataset_User_Agreement.pdf
-rw-r--r-- 1 1000 1000  118863795 Jan 19  2022 yelp_academic_dataset_business.json
-rw-r--r-- 1 1000 1000  286958945 Jan 19  2022 yelp_academic_dataset_checkin.json
-rw-r--r-- 1 1000 1000 5341868833 Jan 19  2022 yelp_academic_dataset_review.json
-rw-r--r-- 1 1000 1000  180604475 Jan 19  2022 yelp_academic_dataset_tip.json
-rw-r--r-- 1 1000 1000 3363329011 Jan 19  2022 yelp_academic_dataset_user.json

root@02c7efc22e05:/workspaces/team-88-project-dva-2023/photos# ls -l
total 35264
-rw-r--r-- 1 1000 1000    80358 Feb 15  2022 Dataset_User_Agreement.pdf
drwxr-xr-x 2 1000 1000 10342400 Feb 15  2022 photos
-rw-r--r-- 1 1000 1000 25653907 Feb 15  2022 photos.json
```

### Building the models

Navigate to the "train" directory and run "python experiments_complete.py 5".  The program will
generate 5 .pkl files in the following format: trained_model_xx.pkl where xx is the name of a city. 
(e.g. trained_model_Philadelphia.pkl)  The model building is complete after all 5 files are 
generated.  Next, in the same directory, run "python experiments_complete.py 6".  The program
will generate a sentiments.pkl file that contains the sentiment analysis data.  This will take
anywhere from 30 mins to an hour depending on the hardware you use.  The run is complete when 
the sentiments.pkl file is generated. The run will also create some .csv files in the format df_{cityname}.csv.
These files will appear in the `./train/` directory.


When you have finished building the models, you should move the .pkl files here: `./utils/pkl_files`
The file setup should look like this:
```
root@02c7efc22e05:/workspaces/team-88-project-dva-2023/utils/pkl_files# ls -l
total 32417944
-rwxr-xr-x 1 root root       58894 Apr 14 16:59 sentiments.pkl
-rwxr-xr-x 1 root root  3382560528 Apr 14 17:03 trained_model_Indianapolis.pkl
-rwxr-xr-x 1 root root 10138832911 Apr 14 17:09 trained_model_Nashville.pkl
-rwxr-xr-x 1 root root  8079844983 Apr 14 17:13 trained_model_Philadelphia.pkl
-rwxr-xr-x 1 root root  7666320520 Apr 14 17:17 trained_model_Tampa.pkl
-rwxr-xr-x 1 root root  3928321204 Apr 14 17:18 trained_model_Tucson.pkl
```

And you should move the df_{cityname}.csv files that indicate which restaurants the model is supported for here: `./yelp_data/`
The file setup should look like this:
```
root@02c7efc22e05:/workspaces/team-88-project-dva-2023/yelp_data# ls -l
total 9108572
-rw-r--r-- 1 1000 1000      80358 Feb 15  2022 Dataset_User_Agreement.pdf
-rwxr-xr-x 1 root root    6014364 Apr 14 20:33 df_Indianapolis.csv
-rwxr-xr-x 1 root root    7871819 Apr 14 20:33 df_Nashville.csv
-rwxr-xr-x 1 root root    8056051 Apr 14 20:33 df_Philadelphia.csv
-rwxr-xr-x 1 root root    7639118 Apr 14 20:33 df_Tampa.csv
-rwxr-xr-x 1 root root    5849379 Apr 14 20:33 df_Tucson.csv
-rw-r--r-- 1 1000 1000  118863795 Jan 19  2022 yelp_academic_dataset_business.json
-rw-r--r-- 1 1000 1000  286958945 Jan 19  2022 yelp_academic_dataset_checkin.json
-rw-r--r-- 1 1000 1000 5341868833 Jan 19  2022 yelp_academic_dataset_review.json
-rw-r--r-- 1 1000 1000  180604475 Jan 19  2022 yelp_academic_dataset_tip.json
-rw-r--r-- 1 1000 1000 3363329011 Jan 19  2022 yelp_academic_dataset_user.json
```

### Running the python-flask API backend

The app can be run in two modes, one with the recommendation engine, and one without.
Running without the recommendation engine is useful if you want to run the app without training the models.
Run without the recommendation engine by running `python app.py` in the terminal
To run with the recommendation engine, run `python app.py -r` in the terminal

### Serving the front-end

To serve the front-end use the built in python server by running `python -m http.server 80`
Navigate to http://localhost/front-end/88_search_bar.html to use the application

### Developing the backend

The backend is mainly contained in the load_data and utils modules and the app.py file. 
Load_data loads the json data from yelp into a sqlite3 database.
Utils contains the rcommendation engine in the utils/recommendation.py file.
App.py contains the API code.
Modify these files to add new functionality or adjust the recommendation engine.

### Developing the front-end

The front-end is contained within the ./front-end/ folder and consists of two .html files and other supporting files. 
The two html files are 88_search_bar.html and restaurant_details.html
Modify them and their supporting files to add or change functionality or design.

### Developing the models

To run the experiments described in our report, navigate to the "train" directory.  Run "python experiments_complete.py X",
where X is 1, 2, 3, or 4.

To determine which CF algorithm works best, run "python experiments_complete.py 1".  The best peforming algorithm is
KNNBaseine.
To determine the best parameters for KNNBaseline, run "python experiments_complete.py 2".  The best parameters are
displayed on the console.
To determine the improvement obtained when using an optimized KNNBaseline (with best parameters) and an unoptimized
KNNBaseline using default params, run "yython experiments_complete.py 3".  The metrics are displayed on the console.
To determine the size of training dataset that your hardware supports, run "python experiments_complete.py 4".  The metrics
are displayed on the console.  Note that this test will result in a segfault as the program terminates when it encounters
an out of memory error (which cannot be caught and handled gracefully).

### Tests

For the python backend, we are using pytest. See documentation: https://docs.pytest.org/en/7.1.x/getting-started.html
To run the tests you can simply type `pytest` into the command line.
To add to tests, look at ./tests/test_app.py as an example and follow the pattern to build more tests.

### Formatting
Pre-commit hooks have been setup that will reformat your python code before allowing you to make a commit. We are using black and isort to make our code look pretty and standardize across the project.
