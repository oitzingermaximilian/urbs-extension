from abc import ABC, abstractmethod
import pyomo.core as pyomo
from pyomo.environ import value


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

        if stf - m.l[location, tech] >= value(m.y0):
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
        return m.capacity_scrap_rec[stf, location, tech] == (
            (m.f_mining[location, tech] / m.f_recycling[location, tech])
            * m.capacity_ext_eusecondary[stf, location, tech]
        )


class capacity_scrap_total_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == value(m.y0):
            return (
                m.capacity_scrap_total[stf, location, tech]
                == m.capacity_scrap_dec[stf, location, tech]
                - m.capacity_scrap_rec[stf, location, tech]
            )
        else:
            return pyomo.Constraint.Skip


class capacity_scrap_total_rule2(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == value(m.y0):
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
        if stf == value(m.y0):
            return pyomo.Constraint.Skip
        else:
            lhs = (
                m.capacity_scrap_rec[stf, location, tech]
                - m.capacity_scrap_rec[stf - 1, location, tech]
            )
            rhs = (
                m.f_increase[location, tech]
                * m.capacity_scrap_rec[stf - 1, location, tech]
            )
            return lhs <= rhs


def apply_scrap_constraints(m):
    constraints = [
        decommissioned_capacity_rule(),
        capacity_scrap_dec_rule(),
        capacity_scrap_rec_rule(),
        capacity_scrap_total_rule(),
        capacity_scrap_total_rule2(),
        cost_scrap_rule(),
        # scrap_total_decrease_rule(),
        scrap_recycling_increase_rule(),
    ]

    m.decommissioned_capacity_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[0].apply_rule(m, stf, loc, tech),
    )
    m.capacity_scrap_dec_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[1].apply_rule(m, stf, loc, tech),
    )
    m.capacity_scrap_rec_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[2].apply_rule(m, stf, loc, tech),
    )
    m.capacity_scrap_total_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[3].apply_rule(m, stf, loc, tech),
    )
    m.capacity_scrap_total_rule2 = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[4].apply_rule(m, stf, loc, tech),
    )
    m.cost_scrap_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[5].apply_rule(m, stf, loc, tech),
    )
    # m.scrap_total_decrease_rule = pyomo.Constraint(
    #    m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[6].apply_rule(m, stf, loc, tech)
    # )
    m.scrap_recycling_increase_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[6].apply_rule(m, stf, loc, tech),
    )
