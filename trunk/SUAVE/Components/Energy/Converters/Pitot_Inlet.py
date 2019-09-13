## @ingroup Components-Energy-Converters
# Pitot_Inlet.py
#
# Created:  May 2019, M. Dethy

# ----------------------------------------------------------------------
#  Imports
# ----------------------------------------------------------------------

import SUAVE

# python imports
from warnings import warn

# package imports
import numpy as np

from SUAVE.Core import Data
from SUAVE.Components.Energy.Energy_Component import Energy_Component
from SUAVE.Methods.Aerodynamics.Common.Gas_Dynamics import Oblique_Shock, Isentropic

# ----------------------------------------------------------------------
#  Pitot Inlet Component
# ----------------------------------------------------------------------
## @ingroup Components-Energy-Converters
class Pitot_Inlet(Energy_Component):
    """This is a pitot inlet component intended for use in compression.
    Calling this class calls the compute function.

    Source:
    https://web.stanford.edu/~cantwell/AA283_Course_Material/AA283_Course_Notes/
    """

    def __defaults__(self):
        """This sets the default values for the component to function.

        Assumptions:
        None

        Source:
        N/A

        Inputs:
        None

        Outputs:
        None

        Properties Used:
        None
        """
        # setting the default values
        self.tag = 'pitot_inlet'
        self.areas                           = Data()
        self.areas.capture                   = 0.0
        self.areas.throat                    = 0.0
        self.areas.inlet_entrance            = 0.0
        self.inputs.stagnation_temperature   = np.array([0.0])
        self.inputs.stagnation_pressure      = np.array([0.0])
        self.outputs.stagnation_temperature  = np.array([0.0])
        self.outputs.stagnation_pressure     = np.array([0.0])
        self.outputs.stagnation_enthalpy     = np.array([0.0])

    def compute(self, conditions):
        
        """ This computes the output values from the input values according to
        equations from the source.

        Assumptions:
        Constant polytropic efficiency and pressure ratio
        Adiabatic

        Source:
        https://web.stanford.edu/~cantwell/AA283_Course_Material/AA283_Course_Notes/

        Inputs:
        conditions.freestream.
          isentropic_expansion_factor         [-]
          specific_heat_at_constant_pressure  [J/(kg K)]
          pressure                            [Pa]
          gas_specific_constant               [J/(kg K)]
        self.inputs.
          stagnation_temperature              [K]
          stagnation_pressure                 [Pa]

        Outputs:
        self.outputs.
          stagnation_temperature              [K]
          stagnation_pressure                 [Pa]
          stagnation_enthalpy                 [J/kg]
          mach_number                         [-]
          static_temperature                  [K]
          static_enthalpy                     [J/kg]
          velocity                            [m/s]

        Properties Used:
        self.
          pressure_ratio                      [-]
          polytropic_efficiency               [-]
          pressure_recovery                   [-]
        """

        # unpack from conditions
        gamma = conditions.freestream.isentropic_expansion_factor
        Cp = conditions.freestream.specific_heat_at_constant_pressure
        Po = conditions.freestream.pressure
        M0 = np.atleast_2d(conditions.freestream.mach_number)
        R = conditions.freestream.gas_specific_constant

        # unpack from inputs
        Tt_in = self.inputs.stagnation_temperature
        Pt_in = self.inputs.stagnation_pressure

        # unpack from self
        A0 = conditions.freestream.area_initial_streamtube
        AE = self.areas.capture # engine face area
        AC = self.areas.throat # narrowest part of inlet
        
        # Compute the mass flow rate into the engine
        T               = Isentropic.isentropic_relations(M0, gamma)[0]*Tt_in
        v               = np.sqrt(gamma*R*T)*M0
        mass_flow_rate  = conditions.freestream.density * A0 * v

        f_M0            = Isentropic.isentropic_relations(M0, gamma)[-1]
        f_ME_isentropic = (f_M0 * A0)/AE
        
        f_MC_isentropic = (f_M0 * A0)/AC
        i_sub_shock     = np.logical_and(M0 <= 1.0, f_MC_isentropic > 1)
        i_sub_no_shock  = np.logical_and(M0 <= 1.0, f_MC_isentropic <= 1)
        i_sup           = M0 > 1.0
        
        if len(Pt_in) == 1:
            Pt_in = np.asscalar(Pt_in)*np.ones_like(M0)
        if len(Tt_in) == 1:
            Tt_in = np.asscalar(Tt_in)*np.ones_like(M0)
            
        # initializing the arrays
        Tt_out  = Tt_in
        ht_out  = Cp*Tt_in
        Pt_out  = np.ones_like(M0)
        Mach    = np.ones_like(M0)
        T_out   = np.ones_like(M0)
        f_ME    = np.ones_like(M0)
        MC      = np.ones_like(M0)
        Pr_c    = np.ones_like(M0)
        Tr_c    = np.ones_like(M0)
        Ptr_c   = np.ones_like(M0)
        f_MC    = np.ones_like(M0)
        
        # Conservation of mass properties to evaluate subsonic case
        Pt_out[i_sub_no_shock]   = Pt_in[i_sub_no_shock]
        f_ME[i_sub_no_shock]     = f_ME_isentropic[i_sub_no_shock]
        Mach[i_sub_no_shock]     = Isentropic.get_m(f_ME[i_sub_no_shock], gamma[i_sub_no_shock], 1)
        T_out[i_sub_no_shock]    = Isentropic.isentropic_relations(Mach[i_sub_no_shock], gamma[i_sub_no_shock])[0]*Tt_out[i_sub_no_shock]

        
        # Analysis of shocks for subsonic flow with shock in inlet
        MC[i_sub_shock], Pr_c[i_sub_shock], Tr_c[i_sub_shock], Ptr_c[i_sub_shock] = Oblique_Shock.oblique_shock_relations(M0[i_sub_shock],gamma[i_sub_shock],0,90*np.pi/180.)
        Pt_out[i_sub_shock] = Ptr_c[i_sub_shock]*Pt_in[i_sub_shock]
        f_MC[i_sub_shock] = Isentropic.isentropic_relations(MC[i_sub_shock], gamma[i_sub_shock])[-1]
        f_ME[i_sub_shock] = f_MC[i_sub_shock]*AC/AE
        
        Mach[i_sub_shock] = Isentropic.get_m(f_ME[i_sub_shock], gamma[i_sub_shock], 1)
        T_out[i_sub_shock] = Isentropic.isentropic_relations(Mach[i_sub_shock], gamma[i_sub_shock])[0]*Tt_out[i_sub_shock]
        
        # Analysis of shocks for the supersonic case
        MC[i_sup], Pr_c[i_sup], Tr_c[i_sup], Ptr_c[i_sup] = Oblique_Shock.oblique_shock_relations(M0[i_sup],gamma[i_sup],0,90*np.pi/180.)
        Pt_out[i_sup] = Ptr_c[i_sup]*Pt_in[i_sup]
        f_MC[i_sup] = Isentropic.isentropic_relations(MC[i_sup], gamma[i_sup])[-1]
        f_ME[i_sup] = f_MC[i_sup]*AC/AE
        
        Mach[i_sup] = Isentropic.get_m(f_ME[i_sup], gamma[i_sup], 1)
        T_out[i_sup] = Isentropic.isentropic_relations(Mach[i_sup], gamma[i_sup])[0]*Tt_out[i_sup]
        
        # -- Compute exit velocity and enthalpy
        h_out = Cp * T_out
        u_out = np.sqrt(2. * (ht_out - h_out))

        # pack computed quantities into outputs
        self.outputs.stagnation_temperature = Tt_out
        self.outputs.stagnation_pressure = Pt_out
        self.outputs.stagnation_enthalpy = ht_out
        self.outputs.mach_number = Mach
        self.outputs.static_temperature = T_out
        self.outputs.static_enthalpy = h_out
        self.outputs.velocity = u_out
        conditions.mass_flow_rate = mass_flow_rate
        
    def compute_drag(self, conditions):
        
        '''
        Nomenclature/labeling of this section is inconsistent with the above
        but is consistent with Nikolai's methodology as presented in aircraft
        design
        '''
        
        
        # Unpack constants from freestream conditions
        gamma       = conditions.freestream.isentropic_expansion_factor
        R           = conditions.freestream.gas_specific_constant
        P_inf       = conditions.freestream.pressure
        M_inf       = np.atleast_2d(conditions.freestream.mach_number)
        rho_inf     = conditions.freestream.density

        # unpack from inputs
        Tt_inf = self.inputs.stagnation_temperature
        Pt_inf = self.inputs.stagnation_pressure
        
        # compute relevant freestream quantities
        T_inf  = Isentropic.isentropic_relations(M_inf, gamma)[0] * Tt_inf
        v_inf  = np.sqrt(gamma*R*T_inf) * M_inf
        q_inf  = 1/2 * rho_inf * v_inf**2
        f_Minf = Isentropic.isentropic_relations(M_inf, gamma)[-1]

        # unpack from self
        A_inf = conditions.freestream.area_initial_streamtube
        AC = self.areas.capture # engine face area
        A1 = self.areas.inlet_entrance # area of the inlet entrance
        AT = self.areas.throat
        
        f_Minf           = Isentropic.isentropic_relations(M_inf, gamma)[-1]
#        i_sub           = M0 <= 1.0
#        i_sup           = M0 > 1.0
        
        f_MT_isentropic = (f_Minf * A_inf)/AT
        i_sub_shock     = np.logical_and(M_inf  <= 1.0, f_MT_isentropic > 1)
        i_sub_no_shock  = np.logical_and(M_inf  <= 1.0, f_MT_isentropic <= 1)
        i_sup           = M_inf  > 1.0
        
        # compute A1 quantities
#        i_sub           = M_inf <= 1.0
#        i_sup           = M_inf > 1.0
        
        # initialize values
        f_M1 = np.ones_like(Tt_inf)
        Pr_1 = np.ones_like(Tt_inf)
        P1   = np.ones_like(Tt_inf)
        M1   = np.ones_like(Tt_inf)
        
        # subsonic case
        f_M1[i_sub_no_shock]      = (f_Minf[i_sub_no_shock] * A_inf[i_sub_no_shock])/A1
        M1[i_sub_no_shock]        = Isentropic.get_m(f_M1[i_sub_no_shock], gamma[i_sub_no_shock], 1)
        P1[i_sub_no_shock]        = Isentropic.isentropic_relations(M1[i_sub_no_shock], gamma[i_sub_no_shock])[1] * Pt_inf[i_sub_no_shock]
        
        # supersonic case
        M1[i_sub_shock], Pr_1[i_sub_shock] = Oblique_Shock.oblique_shock_relations(M_inf[i_sub_shock],gamma[i_sub_shock],0,90*np.pi/180.)[0:2]
        P1[i_sub_shock]              = Pr_1[i_sub_shock]*P_inf[i_sub_shock]
        
        # supersonic case
        M1[i_sup], Pr_1[i_sup] = Oblique_Shock.oblique_shock_relations(M_inf[i_sup],gamma[i_sup],0,90*np.pi/180.)[0:2]
        P1[i_sup]              = Pr_1[i_sup]*P_inf[i_sup]
        
        # get k_add
        c1_list =  [-18.89169518, 71.11608826, -98.78321794, 59.30401343, -12.54234863]
        c2_list = [3.2614414, -15.37113363, 27.9247673, -20.70274059, 4.25466643]
        c3_list = [4.83460478, -16.62737509, 20.6998037, -11.04366207, 2.73090033]
        
        # Get the coefficients for the specified mach number
        c1 = np.polyval(c1_list, M_inf)
        c2 = np.polyval(c2_list, M_inf)
        c3 = np.polyval(c3_list, M_inf)
        
        # Use coefficients on theta_c to get the pressure recovery
        fit   = [c1, c2, c3]

        K_add = np.polyval(fit, A_inf/AC)

        CD_add = (P_inf/q_inf) * (A1/AC) * ((P1/P_inf)*(1+gamma*M1**2)-1) - 2*(A_inf/AC)
        D_add  = CD_add * q_inf* AC * K_add
        
        return D_add
        
    __call__ = compute