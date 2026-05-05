# MSc Sports Biomehcnaics Automated Report Coursework- Automated Baseball Pitch Analysis

### Acknowledgement of data usage
The data for this assignment was taken from Driveline OpenBiomechanics https://github.com/drivelineresearch/openbiomechanics. 

### Limitations
While the team at driveline uses dual force plates at the landing spot to acdomodate pitchers throwing from both sides,I simplified the setup for the purpose of this assignment to include only the rubber force plate and the glove side plate for a right handed pitcher.\
The reason for this is that with a time constraint on the assignment, I did not have time to prepare the program to determine which foot is conencted to which force plate, and update the Opensim external loads file based on this detection. As such,\
I configured the external loads to only apply force through the right calcaneus at the rubber, and left calcaneus at landing.

Because of this, only right handed pitchers landing open will work for this pipeline at this time.\
\
Additionally, at the time of writing, the required Opensim API is not available through pip install, so conda must be installed to create the environment.

### Usage of the program
To use the program, use:\
\
streamlit run app.py \
\
in the terminal, with the directory set to the program folder. Sample data is provided, and should be uploaded to the corresponding drop box with the program running. 
