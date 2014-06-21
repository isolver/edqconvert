===================================
EDQ Result Files Conversion Script
===================================

This folder contains the script used to convert eye samples from 
ioHub DataStore HDF5 files into a "wide" format, where each eye sample
row contains information about the participant, session, eye tracker and 
display equipment used, in addition to the eye sample data itself. 

Part of the conversion process includes only selecting samples that have 
a time stamp within the period a fixation target was visible on the screen.

The output of the script for 2081 of the 2093 HDF5 data files is also included
in the 'output' folder of this directory. 12 of the data files were excluded
because the HDF5 file did not contain any sample data. 

A total of 39,709,344 eye samples were selected and saved to the files. 

It took about 1 hour to convert the 2081 hdf5 files.

Results Files NOT Converted
============================

The following eye tracker model data has not been converted by this script
because the eye data was not saved by ioHub:

    * asl
    * positivescience
    * smietg
    * smihed
    * tobiiglasses
    
The following eye tracker data was not converted because the method of 
converting the analog data into gaze coordinates was not known at the time
of conversion:

    * dpi
    
Converted Data File Types
=========================

The data files are converted into two file types:
    * Tab delimited .txt : plain text files, open with anything, 
      including Excel.
    * NumPy .npy : binary NumPy files. Open using numpy.load()
      http://docs.scipy.org/doc/numpy/reference/generated/numpy.load.html
      The data is returned as a numpy array of structured array elements.

Converted File Format
----------------------

Each saved file represents the data collected from 1 - N sessions / runs of
the test, with one participant using one of the tested eye tracker models.
Most files only have one session, while a minority have > 1 session saved to
the same file. Data from different sessions within a single
output file can be grouped by the session_id column.

Each converted file contain N rows, where N is the number of eye samples that 
occurred within the time period the fixation target was visible at one 
of the 49 target positions presented.

Each converted file has the following columns. In the case of the .txt type, a
header row is written as the first line in the file, providing the name of each
column. For the .npy type files, the column names provided here match the 
element names of each structured numpy array.

	subject_id : ID assigned to a specific participant. 
	display_refresh_rate : Hz update rate of display.
	eyetracker_model : The unique label given to each eye tracker model tested.
	dot_deg_sz : Approximate size of the target in visual degrees.
	eyetracker_sampling_rate : Sampling rate of the eye tracker being used, in Hz.
	eyetracker_mode : The eyes that were being tracked (Binocular, Left Eye, Right Eye)
	fix_stim_center_size_pix : The pixel size of the fixation target inner dot
	operator : Alpha character code assigned to a specific operator performing data collection.
	eyetracker_id : A unique integer ID assigned to each eye tracker.
	display_width_pix : The horizontal resolution of the display in pixels.
	display_height_pix : The vertical resolution of the display in pixels.
	screen_width : The horizontal length of the display in mm.
	screen_height : The vertical length of the display in mm.
	eye_distance : The approximate eye to display center distance in mm.
	SESSION_ID : The ioHub session ID assigned within a given hdf5 file.
	TRIAL_START : The time (in seconds) the fixation target started to be presented at a the given target location.
	TRIAL_END : The time (in seconds) the fixation target was removed from the given target location.
	posx : The horizontal position of the target in pixels. NOTE: The pixel origin ( 0, 0) is the center of the screen.
	posy : The vertical position of the target in pixels. NOTE: The pixel origin ( 0, 0) is the center of the screen.
	dt : The duration the target was presented for (actual presentation time will be a multiple of the display_refresh_rate).
	ROW_INDEX : The ID of the target position being displayed.
	session_id : Same as SESSION_ID.
	device_time : The time of the sample as reported by the eye tracking device.
	time : The time of the sample after being converted to the ioHub time base (in seconds).
	right_gaze_x : Right eye horizontal position in pixels. * 0.0 is screen center.
	right_gaze_y : Right eye vertical position in pixels. * 0.0 is screen center.
	right_pupil_measure1 : Right eye pupil size / diameter. * units are eye tracker model specific.
	left_gaze_x : Left eye horizontal position in pixels. * 0.0 is screen center.
	left_gaze_y : Left eye vertical position in pixels. * 0.0 is screen center.
	left_pupil_measure1 : Left eye pupil size / diameter. * units are eye tracker model specific.
	status : ioHub status field for the sample. 0 = no issues; > 0 = left and/or right eye data is missing.
	target_angle_x :  Horizontal position of target in visual degrees. 0 is screen center.
	target_angle_y :  Vertical position of target in visual degrees. 0 is screen center.
	left_angle_x :  Left eye horizontal position in visual degrees. 0 is screen center.
	left_angle_y :  Left eye vertical position in visual degrees. 0 is screen center.
	right_angle_x : Right eye horizontal position in visual degrees. 0 is screen center.
	right_angle_y : Right eye vertical position in visual degrees. 0 is screen center.

Missing Position Data Values
----------------------------- 

The value saved to the eye position gaze x and y columns is dependant on the 
eye tracker model the data as collected from:

    eyefollower: 0
    eyelink : 0
    eyetribe : -840 for x, 
                525 for y
    hispeed1250 : 0 
    hispeed240 : 0
    red250 : 0
    red500 : 0
    redm : 0
    t60xl : -1
    tx300 : -1
    x2 : -1
      
Running Conversion Script Locally
==================================

To run the script you will need the software listed in the Installation section,
as well as the EDQ HDF5 files, organized as described in the Expected Folder / 
File Structure section. The archive file containing the data is already in this
file structure, so you should not have to rearrange data files.  

Starting the Conversion Program
--------------------------------

Open the run_conversion.py file in your python IDE of choice and run it

or

Open a command prompt / terminal window, and type the following:

    cd [path to the directory this file is in]
    python.exe run_conversion.py

Expected Folder / File Structure 
---------------------------------

To run the script you will need the software listed in the Installation section,
as well as the EDQ HDF5 files. 

The HDF5 files must be in a folder called sample_data in the same directory as 
the run_conversion.py script. The sample_data folder must have the following structure:

sample_data
   |
   |--[eye tracker name 1]
   |     |
   |     |--[date1]
   |     |    |
   |     |    |-- events_XX.hdf5
   |     |    |-- ....
   |     |    |-- events_NN.hdf5
   |     |
   |     |-- ....
   |     |
   |     |--[dateN]
   |          |
   |          |-- events_XX.hdf5
   |          |-- ....
   |          |-- events_NN.hdf5
   |
   |-- ......
   |
   |   
   |--[eye tracker name N]   
   |     |
   |     |-- .....
   |     |    |
   |     |    |-- ......

Installation
-------------

To run edg2txt.py, the following software must be installed. 

Python 2.7.x: https://www.python.org/

Python Packages
~~~~~~~~~~~~~~~~

PyTables 3.0+: http://pytables.github.io/downloads.html
Numexpr 2.4: https://code.google.com/p/numexpr/
NumPy 1.8.1: http://www.numpy.org/

Free Python Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~
 
If you do not have a python environment already setup on your computer,
there are several python distributions that also include all the 
Python Packages needed:

Linux, Windows, OSX Support
++++++++++++++++++++++++++++

Anaconda: https://store.continuum.io/cshop/anaconda/ 
Enthought Canopy: https://www.enthought.com/products/canopy/
ActiveState: http://www.activestate.com/activepython

Windows Only
+++++++++++++

WinPython: http://winpython.sourceforge.net/
PythonXY: http://code.google.com/p/pythonxy


