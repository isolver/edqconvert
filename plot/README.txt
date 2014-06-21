edqplot
========

edqplot.py is a script that will display the eye sample data loaded from a .npy data file that has been created by edqconvert.

It is very basic right now:

* Can open one file at a time.
* No saving of anything.
* Provides a trace plot of the eye sample data in the file.
   * left and right eye position  (in degrees)
   * position of fixation target used in the task
   * Contains a selection region, which controls the data displayed in a second, magnified , trace plot.
   * Selection region can be moved and resized using the mouse on the region graphic itself.

By default all 'trials' of session 1 are displayed, where a trial is the fixation
target presentation at 1 of the 49 positions. A smaller subset of the trials within
a session can be used. To do so

1. Click on the Settings tab in the edqplot window.
2. Change the **Eye Sample Selection -> Target Display Index Selection** section of preferences.

   * First Target Index : Specified where the sample
     data should start from based on the target onset time
     of the specified trial index.
   * Plot Target Count: Specifies how many target position changes should be
     plotted from 'First Target Index'
     
Using the software
-------------------

If you have a python 2.7 distribution installed that can run psychopy, you likely have most packages needed.

* Check that pyqt4 is installed and add it if it is not. 

* Install pyqtgraph (www.pyqtgraph.org) by downloading the 
  latest package source from https://github.com/pyqtgraph/pyqtgraph. 
  Download the zip of the package, unarchive, and run ```python setup.py install``.
  
To start edqplot, launch the edqplot.py script from your fav. python IDE or from a command prompt.

Windows, Linux, and OSX should all work, although only tested on Windows right now.

TO DO
--------

After playing with the app, it will become obvious that there is still
a lot of work to do so that edqplot is a useful tool, not just a cute one.

Contibutors should discuss what functionality should be added based on priority. 
Let me know what you think and how you think we should move this forward.

License
----------

edqconvert and edqplot are GPL v3 licensed.

The developers of the software make no warrant about the software of any kind.
Use at your own pleasure AND risk.

