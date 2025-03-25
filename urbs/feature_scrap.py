from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, *args):
        pass


class decommissioned_capacity_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
           Determines the decommissioned capacity for a given technology at a specific
           location and time step. Adjusts calculations based on whether the technology is
           solar PV or another type.

           Args:
               m: The model containing all relevant data and parameters.
               stf: The time step for which the capacity rule is being applied.
               location: The specific location of the technology being evaluated.
               tech: The technology type (e.g., "solarPV", other).

           Returns:
               A rule that specifies the decommissioned capacity in the model, based
               on the defined conditions and parameters.
           """
        if tech == "solarPV":
            _exogenous = 7.5 * 1000
        if tech == "windon":
            _exogenous = 5 * 1000
        else:
            _exogenous = 2 * 1000

        if stf - m.l[location, tech] >= m.y0:
            return (
                    m.capacity_dec[stf, location, tech]
                    == m.capacity_ext_new[stf - m.l[location, tech], location, tech]
            )
        else:
            return (
                    m.capacity_dec[stf, location, tech]
                    == _exogenous + 0.00000015 * m.capacity_ext_new[stf, location, tech]
            # TODO change back multiplier - currently problems with solar being to much decommissioned
            )


class capacity_scrap_dec_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Defines the scrap decision rule for capacity reduction within a specified technological,
        staffing, and locational context. This function ensures that the scrap capacity value is
        proportional to the decrement in capacity based on a scrap factor.

        Args:
            m: A model object that contains variables and parameters related to capacities, scrap
               factors, and decisions.
            stf: The staff category under consideration.
            location: The geographical location under consideration.
            tech: The technological category under consideration.

        Returns:
            The logical equality constraint ensuring that the scrap decision is proportional to
            the decrement in capacity as determined by the scrap factor.
        """
        return (
                m.capacity_scrap_dec[stf, location, tech]
                == m.f_scrap[location, tech] * m.capacity_dec[stf, location, tech]
        )


class capacity_scrap_rec_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Defines a rule to ensure the relationship between capacity of scrap recovery and
        other related parameters and variables in the system.

        This rule enforces that the capacity of scrap recovery for a specific staff unit
        (stf), location, and technology equals the calculated value based on the mining
        factor, recycling factor, and secondary external use capacity.

        Args:
            m: The model instance that holds parameters, variables, and constraints
                for the optimization problem.
            stf: Specific staff unit considered in the system.
            location: Location where the operation takes place.
            tech: Technology associated with the considered operation.

        Returns:
            A Boolean expression representing the equality constraint for the rule.
        """
        return m.capacity_scrap_rec[stf, location, tech] == (
                (m.f_mining[location, tech] / m.f_recycling[location, tech])
                * m.capacity_ext_eusecondary[stf, location, tech]
        )


class capacity_scrap_total_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Determines whether the total scrap capacity constraint for a specified staff,
        location, and technology should be applied or skipped.

        This function establishes a relationship between total scrap capacity,
        scrap capacity decommissioned, and scrap capacity recovered for a
        specific combination of staff, location, and technology. If the specified
        staff parameter (stf) matches the base year (m.y0), the function
        returns a condition for the corresponding total scrap capacity rule.
        Otherwise, it skips the application of this constraint.

        Args:
            m: A Pyomo model instance.
            stf: Staff parameter to check against the model's base year.
            location: Geographical or functional location identifier.
            tech: Technological category or identifier.

        Returns:
            Constraint or a value indicating to skip application of the constraint.
        """
        if stf == m.y0:
            return (
                    m.capacity_scrap_total[stf, location, tech]
                    == m.capacity_scrap_dec[stf, location, tech]
                    - m.capacity_scrap_rec[stf, location, tech]
            )
        else:
            return pyomo.Constraint.Skip


class capacity_scrap_total_rule2(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Determines and enforces the total capacity scrap rule for the given parameters. This function is used
        to skip the constraint for the initial stage (y0) or enforce the constraint for subsequent stages.
        The constraint ensures that the capacity scrap total for a given staffing (stf), location, and
        technology (tech) is updated based on the capacity scrap decrease and reception.

        Args:
            m: The Pyomo model object containing the variables and parameters for the constraint.
            stf: An integer representing the staffing stage.
            location: The spatial location corresponding to the current calculation.
            tech: The type of technology associated with the model.

        Returns:
            pyomo.Constraint.Skip if the staffing stage equals the initial value (m.y0), else the
            equality constraint for capacity scrap total is returned.
        """
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            return (
                    m.capacity_scrap_total[stf, location, tech]
                    == m.capacity_scrap_total[stf - 1, location, tech]
                    + m.capacity_scrap_dec[stf, location, tech]
                    - m.capacity_scrap_rec[stf, location, tech]
            )


class cost_scrap_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Calculates the scrap cost rule based on the scrap recovery factor and the corresponding
        recovery capacity for a particular scenario.

        The function enforces that the scrap cost for a given staff, location, and technology
        is equivalent to the product of the scrap recovery factor and the scrap recovery
        capacity for the same criteria.

        Args:
            m: Model object containing relevant parameters and constraints.
            stf: Staff identifier.
            location: Location identifier.
            tech: Technology identifier.

        Returns:
            A boolean expression that validates the relationship between
            the scrap cost, scrap recovery factor, and recovery capacity.
        """
        return (
                m.cost_scrap[stf, location, tech]
                == m.f_scrap_rec[stf, location, tech]
                * m.capacity_scrap_rec[stf, location, tech]
        )


class scrap_total_decrease_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Computes and enforces a rule that ensures the total scrap capacity decreases or
        remains constant over sequential time steps.

        This constraint is applied to maintain consistency of scrap capacity data across
        different states or time frames. The function skips the constraint for the initial
        state.

        Args:
            m: The Pyomo model object containing variables and constraints.
            stf: The current state or time frame being evaluated.
            location: The specific location for which the scrap capacity rule is applied.
            tech: The specific technology associated with the scrap capacity.

        Returns:
            Constraint.Skip if the current state or time frame is the initial period,
            otherwise returns an inequality constraint ensuring that the scrap capacity
            at the current state or time does not exceed that of the previous state or
            time.
        """
        if tech == "solarPV":
            if stf <= 2030:
                return pyomo.Constraint.Skip
            else:
                return (
                        m.capacity_scrap_total[stf, location, tech]
                        <= m.capacity_scrap_total[stf - 1, location, tech]
                )
        else:
            return pyomo.Constraint.Skip


class scrap_recycling_increase_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Implements a Pyomo constraint rule to impose a limit on the increase in scrap recycling
        capacity at a specific location and technology between consecutive simulation timeframes.
        The rule ensures that the increase in capacity does not exceed a predefined fraction
        (`f_increase`) of the capacity in the preceding simulation timeframe.

        Args:
            m: Pyomo model representing the optimization problem, containing all relevant
                parameters, variables, and constraints.
            stf: Simulation timeframe, an integer representing the specific period for which
                the constraint is applied.
            location: String or identifier representing the specific location where the constraint is evaluated.
            tech: String or identifier representing the specific technology associated with
                the recycling process being modeled.

        Returns:
            Pyomo.Constraint.Skip: Skips constraint evaluation if the current timeframe (`stf`)
                is the initialization time (`y0`).
            Expression: A constraint ensuring that the change in capacity for the specified
                location and technology at the current timeframe conforms to the predefined
                limit, compared to the preceding timeframe.
        """
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            lhs = (
                    m.capacity_scrap_rec[stf, location, tech]
                    - m.capacity_scrap_rec[stf - 1, location, tech]
            )
            rhs = (
                    m.f_increase[location, tech] * m.capacity_scrap_rec[stf - 1, location, tech]
            )
            return lhs <= rhs


def apply_scrap_constraints(m):
    constraints = [
        DecommissionedCapacityRule(),
        CapacityScrapDecRule(),
        CapacityScrapRecRule(),
        CapacityScrapTotalRule(),
        CapacityScrapTotalRule2(),
        CostScrapRule(),
        ScrapTotalDecreaseRule(),
        ScrapRecyclingIncreaseRule(),
    ]


    m.decommissioned_capacity_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[0].apply_rule(m, stf, loc, tech)
    )
    m.capacity_scrap_dec_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[1].apply_rule(m, stf, loc, tech)
    )
    m.capacity_scrap_rec_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[2].apply_rule(m, stf, loc, tech)
    )
    m.capacity_scrap_total_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[3].apply_rule(m, stf, loc, tech)
    )
    m.capacity_scrap_total_rule2 = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[4].apply_rule(m, stf, loc, tech)
    )
    m.cost_scrap_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[5].apply_rule(m, stf, loc, tech)
    )
    m.scrap_total_decrease_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[6].apply_rule(m, stf, loc, tech)
    )
    m.scrap_recycling_increase_rule = pyomo.Constraint(
        m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[7].apply_rule(m, stf, loc, tech)
    )