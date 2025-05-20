from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, *args):
        pass


class net_zero_industrialactbenchmark_rule_a(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        lhs = (
            m.capacity_ext_euprimary[stf, location, tech]
            + m.capacity_ext_eusecondary[stf, location, tech]
            + m.capacity_ext_stockout[stf, location, tech]
            - m.capacity_ext_stock_imported[stf, location, tech]
        )

        rhs = 0.4 * m.capacity_ext_new[stf, location, tech]

        # Print both sides for debugging
        # print(
        #    f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
        # )

        return lhs >= rhs


def apply_scenario_constraints(m):
    constraints = [net_zero_industrialactbenchmark_rule_a()]

    m.net_zero_industrialactbenchmark_rule_a = pyomo.Constraint(
        m.stf,
        m.location,
        m.tech,
        rule=lambda m, stf, loc, tech: constraints[0].apply_rule(m, stf, loc, tech),
    )
