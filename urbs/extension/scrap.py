from abc import ABC, abstractmethod
import pyomo.core as pyomo
from pyomo.environ import value


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, stf, location, tech):
        pass


class decommissioned_capacity_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Determines the decommissioned capacity for a given technology at a specific
        location and time step. Adjusts calculations based on whether the technology is
        solar PV or another type.
        """
        # Set exogenous value based on technology type
        if tech == "solarPV":
            _exogenous = 7.5 * 1000
        elif tech == "windon":
            _exogenous = 5 * 1000
        elif tech == "windoff":
            _exogenous = 5 * 1000
        else:
            _exogenous = 2 * 1000

        # Condition to determine decommissioning logic
        if stf - m.l[location, tech] >= value(m.y0):
            return (
                m.capacity_dec[stf, location, tech]
                == m.capacity_ext_new[stf - m.l[location, tech], location, tech]
            )
        else:
            return (
                m.capacity_dec[stf, location, tech]
                == _exogenous  # + 0.000015 * m.capacity_ext_new[stf, location, tech]
            )


class capacity_scrap_dec_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        return (
            m.capacity_scrap_dec[stf, location, tech]
            == m.f_scrap[location, tech] * m.capacity_dec[stf, location, tech]
        )


class capacity_scrap_rec_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        var = m.capacity_scrap_rec[stf, location, tech]
        cal = ((m.f_mining[location, tech] / m.f_recycling[location, tech]) * m.capacity_ext_eusecondary[stf, location, tech])

        return var == cal



class capacity_scrap_total_rule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            return (
                m.capacity_scrap_total[stf, location, tech]
                == m.capacity_scrap_dec[stf, location, tech]
                - m.capacity_scrap_rec[stf, location, tech]
            )
        elif stf == value(m.y0):
            return (
                m.capacity_scrap_total[stf, location, tech]
                == m.scrap_total[location, tech]
                + m.capacity_scrap_dec[stf, location, tech]
                - m.capacity_scrap_rec[stf, location, tech]
            )
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


#class scrap_total_decrease_rule(AbstractConstraint):
#    def apply_rule(self, m, stf, location, tech):
#        if tech == "solarPV":
#            if stf <= 2030:
#                return pyomo.Constraint.Skip
#            else:
#                return (
#                    m.capacity_scrap_total[stf, location, tech]
#                    <= m.capacity_scrap_total[stf - 1, location, tech]
#                )
#        else:
#            return pyomo.Constraint.Skip


#class scrap_recycling_increase_rule(AbstractConstraint):
#    def apply_rule(self, m, stf, location, tech):
#        if stf == value(m.y0):
#            return pyomo.Constraint.Skip
#        else:
#            lhs = (
#                m.capacity_scrap_rec[stf, location, tech]
#                - m.capacity_scrap_rec[stf - 1, location, tech]
#            )
#            rhs = (
#                m.f_increase[location, tech]
#                * m.capacity_scrap_rec[stf - 1, location, tech]
#            )
#            return lhs <= rhs


def apply_scrap_constraints(m):
    constraints = [
        decommissioned_capacity_rule(),
        capacity_scrap_dec_rule(),
        capacity_scrap_rec_rule(),
        capacity_scrap_total_rule(),
        cost_scrap_rule(),
        # scrap_total_decrease_rule(),
        # scrap_recycling_increase_rule(),
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
    m.cost_scrap_rule = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[4].apply_rule(m, stf, loc, tech),
    )
    # m.scrap_total_decrease_rule = pyomo.Constraint(
    #    m.stf, m.location, m.tech, rule=lambda m, stf, loc, tech: constraints[5].apply_rule(m, stf, loc, tech)
    # )
    # m.scrap_recycling_increase_rule = pyomo.Constraint(
    #    m.stf,
    #    m.location,
    #    m.tech,
    #    rule=lambda m, stf, loc, tech: constraints[6].apply_rule(m, stf, loc, tech),
    # )
