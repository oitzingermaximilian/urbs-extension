from abc import ABC, abstractmethod
import pyomo.core as pyomo
from pyomo.environ import value


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, *args):
        pass


DEBUG = False  # Set True to enable debug logs


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class costsavings_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        pricereduction_value_sec = sum(
            m.P_sec[location, tech, n] * m.BD_sec[stf, location, tech, n]
            for n in m.nsteps_sec
        )
        expr = m.pricereduction_sec[stf, location, tech] == pricereduction_value_sec
        debug_print(
            f"[costsavings] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"pricereduction_value_sec={pricereduction_value_sec}\n"
            f"    expr: {expr}"
        )
        return expr


class BD_limitation_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        bd_sum_value_sec = sum(m.BD_sec[stf, location, tech, n] for n in m.nsteps_sec)
        expr_ok = bd_sum_value_sec <= 1
        debug_print(
            f"[BD_limitation] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"bd_sum_value_sec={bd_sum_value_sec} <= 1? {expr_ok}"
        )
        return expr_ok


class relation_pnew_to_pprior_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == 2024:
            debug_print(f"[relation_pnew] STF={stf} (2024) ➞ SKIP")
            return pyomo.Constraint.Skip

        if stf == value(m.y0):
            lhs = m.pricereduction_sec[stf, location, tech]
            rhs = m.pricereduction_sec_init[location, tech]
            expr = lhs >= rhs
            debug_print(
                f"[relation_pnew-init] STF={stf} == y0 ➞ {lhs} >= {rhs} ? {expr}"
            )
        else:
            lhs = m.pricereduction_sec[stf, location, tech]
            rhs = m.pricereduction_sec[stf - 1, location, tech]
            expr = lhs >= rhs
            debug_print(
                f"[relation_pnew-recursive] STF={stf} ➞ {lhs} >= {rhs} ? {expr}"
            )
        return expr


class q_perstep_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Ensures cumulative capacity (carryover + yearly extensions from y0 to y)
        meets step requirements in year y.
        """
        y0 = min(m.stf)  # First model year

        # LHS = Carryover (only added once) + sum of extensions from y0 to stf

        lhs = m.total_secondary_cap_inital[location, tech] + sum(
            m.capacity_ext_eusecondary[year, location, tech]
            for year in m.stf
            if y0 <= year <= stf
        )

        # RHS = Sum of required steps for current year
        rhs = sum(
            m.BD_sec[stf, location, tech, n] * m.capacityperstep_sec[location, tech, n]
            for n in m.nsteps_sec
        )

        # Debug output
        expr = lhs >= rhs
        debug_print(
            f"[q_perstep] STF={stf}, loc={location}, tech={tech}  ➞\n"
            f"    LHS={lhs}\n"
            f"    RHS={rhs}, expr: {expr}"
        )

        return expr


class upper_bound_z_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech, nsteps_sec):
        """
        Evaluates whether the left-hand side of the equation for the secondary upper bound
        constraint is less than or equal to the right-hand side. The equation verifies
        constraints in a secondary process model using provided variables and model parameters.

        Args:
            m: The model object containing relevant decision variables and parameters.
            stf: The time step
            location: The geographical or spatial identifier for the context of the calculation.
            tech: The technology type involved in the computation.
            nsteps_sec: The step in the secondary process sequence for which the constraint
                is being evaluated.

        Returns:
            bool: True if the left-hand side value is less than or equal to the right-hand side
                value of the constraint, otherwise False.
        """
        lhs_value = (
            m.BD_sec[stf, location, tech, nsteps_sec]
            * m.capacity_ext_eusecondary[stf, location, tech]
        )
        rhs_value = m.gamma_sec * m.BD_sec[stf, location, tech, nsteps_sec]

        # Debug: Print the left-hand side and right-hand side for upper bound comparison
        # print(
        #    f"Debug: upper_bound_z_eq_sec for stf={stf}, nsteps_sec={nsteps_sec}: LHS = {lhs_value}, RHS = {rhs_value}"
        # )
        expr = lhs_value <= rhs_value
        debug_print(
            f"[upper_bound_z] STF={stf}, step={nsteps_sec}  ➞ "
            f"LHS={lhs_value}, RHS={rhs_value}, expr: {expr}"
        )
        return expr


class upper_bound_z_q1_eq_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech, nsteps_sec):
        """
        Ensures that the left-hand side (LHS) value calculated using the model's boundary
        data and capacity values for the specified secondary step does not exceed the
        right-hand side (RHS) value representing the total possible capacity for the
        configuration provided.

        This function is typically used in optimization or constraint checks within
        models and verifies compliance with an upper bound constraint.

        Args:
            m: The model object containing all relevant parameters and data structures.
            stf: The time step
            location: The identifier for the specific geographic or operational location.
            tech: The identifier for the specific technology or equipment set.
            nsteps_sec: The secondary step number or identifier in the process sequence.

        Returns:
            bool: True if the LHS value does not exceed the RHS value, indicating that
            the upper bound constraint is satisfied; otherwise, False.
        """

        lhs_value = (
            m.BD_sec[stf, location, tech, nsteps_sec]
            * m.capacity_ext_eusecondary[stf, location, tech]
        )
        rhs_value = m.capacity_ext_eusecondary[stf, location, tech]

        # Debug: Print the left-hand side and right-hand side for upper bound comparison
        # print(
        #    f"Debug: upper_bound_z_q1_eq_sec for stf={stf}, nsteps_sec={nsteps_sec}: LHS = {lhs_value}, RHS = {rhs_value}"
        # )
        expr = lhs_value <= rhs_value
        debug_print(
            f"[upper_bound_z_q1] STF={stf}, step={nsteps_sec}  ➞ "
            f"LHS={lhs_value}, RHS={rhs_value}, expr: {expr}"
        )

        return expr


class lower_bound_z_eq_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech, nsteps_sec):
        """
        Compares the lower bound equation for secondary capacity extension in a given
        location, scenario, and time step. The function asserts whether the computed lower
        bound inequality holds by comparing the left-hand side (LHS) against the right-hand
        side (RHS) of the condition.

        Args:
            m: The model object containing system parameters, variables, and coefficients
                necessary for the capacity computation.
            stf: The time step
            location: The string or numerical identifier for the geographical location where
                the secondary capacity extension is being considered.
            tech: The string or numerical identifier representing the technology for which
                the secondary capacity extension is analyzed.
            nsteps_sec: The integer denoting the specific time step in the sequence relevant
                to the secondary capacity computation.

        Returns:
            bool: True if the lower bound inequality holds, otherwise False. The result
                indicates whether the LHS of the inequality is greater than or equal to the RHS.
        """

        lhs_value = (
            m.BD_sec[stf, location, tech, nsteps_sec]
            * m.capacity_ext_eusecondary[stf, location, tech]
        )
        rhs_value = (
            m.capacity_ext_eusecondary[stf, location, tech]
            - (1 - m.BD_sec[stf, location, tech, nsteps_sec]) * m.gamma_sec
        )

        # Debug: Print the left-hand side and right-hand side for lower bound comparison
        # print(
        #    f"Debug: lower_bound_z_eq_sec for stf={stf}, nsteps_sec={nsteps_sec}: LHS = {lhs_value}, RHS = {rhs_value}"
        # )

        expr = lhs_value >= rhs_value
        debug_print(
            f"[lower_bound_z] STF={stf}, step={nsteps_sec}  ➞ "
            f"LHS={lhs_value}, RHS={rhs_value}, expr: {expr}"
        )
        return expr


class non_negativity_z_eq_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech, nsteps_sec):
        """
        Ensures non-negativity of a secondary use-related variable for the specified
        staff, location, technology, and step in the secondary stage.

        This function calculates the left-hand side (LHS) value based on the product
        of a decision variable and capacity, ensuring that the resulting value is
        non-negative. It serves as a constraint validation function for specific
        optimization or computational models.

        Debug information, including the value of the LHS, is printed to assist in
        debugging or analysis of the computation.

        Args:
            m: Model object containing the decision variables and data required
                for computing the constraint.
            stf: The time step
            location: Identifier for the location or facility in the computation.
            tech: Identifier for the specific technology being referenced.
            nsteps_sec: Integer or identifier representing the step in the secondary
                stage.

        Returns:
            bool: True if the LHS value is greater than or equal to zero, indicating
            non-negativity; otherwise, False.
        """

        lhs_value = (
            m.BD_sec[stf, location, tech, nsteps_sec]
            * m.capacity_ext_eusecondary[stf, location, tech]
        )

        # Debug: Print the value of the non-negativity constraint
        # print(
        #    f"Debug: non_negativity_z_eq_sec for stf={stf}, nsteps_sec={nsteps_sec}: LHS = {lhs_value}"
        # )

        expr = lhs_value >= 0
        debug_print(
            f"[non_negativity] STF={stf}, step={nsteps_sec}  ➞ "
            f"LHS={lhs_value}, expr: {expr}"
        )
        return expr


def apply_combined_lr_constraints(m):
    constraints_rm1 = [
        costsavings_constraint_sec(),
        BD_limitation_constraint_sec(),
        relation_pnew_to_pprior_constraint_sec(),
        q_perstep_constraint_sec(),
    ]

    constraints_rm2 = [
        upper_bound_z_constraint_sec(),
        upper_bound_z_q1_eq_sec(),
        lower_bound_z_eq_sec(),
        non_negativity_z_eq_sec(),
    ]

    for i, constraint in enumerate(constraints_rm1):
        constraint_name = f"constraint_rm1_{i + 1}"
        setattr(
            m,
            constraint_name,
            pyomo.Constraint(
                m.stf,
                m.location,
                m.tech,
                rule=lambda m, stf, loc, tech: constraint.apply_rule(m, stf, loc, tech),
            ),
        )

    for i, constraint in enumerate(constraints_rm2):
        constraint_name = f"constraint_rm2_{i + 1}"
        setattr(
            m,
            constraint_name,
            pyomo.Constraint(
                m.stf,
                m.location,
                m.tech,
                m.nsteps_sec,
                rule=lambda m, stf, loc, tech, nsteps_sec: constraint.apply_rule(
                    m, stf, loc, tech, nsteps_sec
                ),
            ),
        )
