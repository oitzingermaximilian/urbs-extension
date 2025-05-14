from abc import ABC, abstractmethod
import pyomo.core as pyomo
from pyomo.environ import value


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, *args):
        pass


class costsavings_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Calculates and verifies the price reduction for a specific staff, location, and
        technology combination based on the provided model's parameters.

        This function computes the sum of product values from the `P_sec` and `BD_sec`
        attributes of the model over a range of steps (`nsteps_sec`). The calculated
        value is then checked against a predefined `pricereduction_sec` value to assert
        its correctness.

        Args:
            m: The optimization model containing attributes such as `P_sec`, `BD_sec`,
                `nsteps_sec`, and `pricereduction_sec`.
            stf: The time step
            location: The location identifier associated with the calculation.
            tech: The technology identifier used in the calculation.

        Returns:
            A boolean expression asserting if the calculated price reduction matches
            the predefined value in the model.
        """
        # Debug statement to check the components of the sum
        pricereduction_value_sec = sum(
            m.P_sec[n, tech, location] * m.BD_sec[stf, location, tech, n]
            for n in m.nsteps_sec
        )
        print(
            f"Calculated pricereduction for {stf}, {location}, {tech}: {pricereduction_value_sec}"
        )

        return m.pricereduction_sec[stf, location, tech] == pricereduction_value_sec


class BD_limitation_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Calculates and enforces the rule for BD limitation by ensuring the sum of BD values
        across all applicable steps does not exceed a specified upper bound.

        This function aggregates the values of the `BD_sec` parameter across all steps
        (`m.nsteps_sec`) for a specific staff (`stf`), location (`location`), and technology
        (`tech`). If the computed sum is less than or equal to 1, the rule is satisfied.

        Args:
            m: The model containing the decision variables and parameters required for
                the calculation.
            stf: The time step
            location: The location identifier within the model as a dimension in
                `BD_sec`.
            tech: The technology identifier within the model as a dimension in
                `BD_sec`.

        Returns:
            bool: True if the sum of the BD values is less than or equal to 1, indicating
                that the limitation rule is satisfied. False otherwise.
        """
        # Debug statement to print the sum of BD[stf, n]
        bd_sum_value_sec = sum(m.BD_sec[stf, location, tech, n] for n in m.nsteps_sec)
        # print(
        #    f"BD_limitation_rule for stf={stf}, Location={location}, Tech={tech}: Sum of BD is {bd_sum_value_sec}"
        # )

        return bd_sum_value_sec <= 1


class relation_pnew_to_pprior_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Applies price reduction relationship constraint with debug output for
        validation.
        """
        if stf == 2024:
            print(f"Skipping constraint for stf={stf} (global start year)")
            return pyomo.Constraint.Skip

        elif stf == value(m.y0):
            p_r_new = m.pricereduction_sec[stf, location, tech]
            p_r_prior = m.pricereduction_sec_init[location, tech]
            print(f"[Initial] stf={stf} == y0={value(m.y0)}: Using INIT condition")
            print(
                f"    pricereduction_sec[{stf}, {location}, {tech}] >= pricereduction_sec_init[{location}, {tech}]"
            )
            return p_r_new >= p_r_prior

        else:
            p_r_new = m.pricereduction_sec[stf, location, tech]
            p_r_prev = m.pricereduction_sec[stf - 1, location, tech]
            print(f"[Recursive] stf={stf}: Comparing with stf-1={stf - 1}")
            print(
                f"    pricereduction_sec[{stf}, {location}, {tech}] >= pricereduction_sec[{stf - 1}, {location}, {tech}]"
            )
            return p_r_new >= p_r_prev


class q_perstep_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Ensures cumulative capacity (carryover + yearly extensions from y0 to y)
        meets step requirements in year y.
        """
        y0 = min(m.stf)  # First model year

        # LHS = Carryover (only added once) + sum of extensions from y0 to stf
        lhs = m.secondary_cap_carryover[location, tech] + sum(
            m.capacity_ext_eusecondary[year, location, tech]
            for year in m.stf
            if y0 <= year <= stf
        )

        # RHS = Sum of required steps for current year
        rhs = sum(
            m.BD_sec[stf, location, tech, n] * m.capacityperstep_sec[n, location, tech]
            for n in m.nsteps_sec
        )

        # Debug output
        print(
            f"Year {stf} ({location}, {tech}):\n"
            f"  Carryover: {m.secondary_cap_carryover[location, tech]}\n"
            f"  Extensions ({y0}-{stf}): {[m.capacity_ext_eusecondary[y, location, tech] for y in m.stf if y0 <= y <= stf]}\n"
            f"  Total LHS: {lhs}\n"
            f"  RHS: {rhs} (Steps: {[m.capacityperstep_sec[n, location, tech] for n in m.nsteps_sec]})"
        )

        return lhs >= rhs


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

        return lhs_value <= rhs_value


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

        return lhs_value <= rhs_value


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

        return lhs_value >= rhs_value


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

        return lhs_value >= 0


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
