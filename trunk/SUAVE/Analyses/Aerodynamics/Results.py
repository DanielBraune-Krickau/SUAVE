## @ingroup Analyses-Aerodynamics
# Results
# Created:   Trent, Jan 2014
# Modified:  Andrew Wendorff, Feb 2016

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

<<<<<<< HEAD
from SUAVE.Analyses import Results as Base_Results
import autograd.numpy as np 
=======
from SUAVE.Core import Data
import numpy as np
>>>>>>> develop

# ----------------------------------------------------------------------
#  Default Aerodynamic Results
# ----------------------------------------------------------------------


default_result = np.zeros([1,1])
## @ingroup Analyses-Aerodynamics
class Results(Data):
    """A class for storing aerodynamic results.

    Assumptions:
    None

    Source:
    N/A
    """      
    def __defaults__(self):
        """This sets the default values for the results.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        N/A
        """               
        self.lift_coefficient  = default_result * 0.
        self.drag_coefficient  = default_result * 0.
        
        self.lift_force_vector = default_result * 0.
        self.drag_force_vector = default_result * 0.
