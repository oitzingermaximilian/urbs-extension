from abc import ABC, abstractmethod
import pyomo.core as pyomo

#ToDo fix this script. It breaks the model into remanufacturing wind

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
        print(
            f"BD_limitation_rule for stf={stf}, Location={location}, Tech={tech}: Sum of BD is {bd_sum_value_sec}"
        )

        return bd_sum_value_sec <= 1


class relation_pnew_to_pprior_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Determines the relationship between the price reductions of the current and
        previous time steps in a secondary context and returns a Pyomo constraint.

        The function ensures that the price reduction for a given time step is greater
        than or equal to the price reduction in the prior time step, given specific
        location and technology.

        Args:
            m: The model containing relevant Pyomo variables and parameters,
                including `pricereduction_sec` and `y0`.
            stf: The time step
            location: The specific location for evaluating the price reduction.
            tech: The technology type associated with the price reduction.

        Returns:
            Either a constraint enforcing the relationship between the current and
            prior time step's price reductions, or skips the constraint for the first
            time step.
        """
        if stf == m.y0:
            # Skip for the first time step
            return pyomo.Constraint.Skip
        else:
            # Debug: Print the comparison between current and previous pricereduction
            print(
                f"Debug: relation_pnew_to_pprior_sec for stf={stf}: pricereduction[{stf}] = {m.pricereduction_sec[stf, location, tech]}, pricereduction[{stf - 1}] = {m.pricereduction_sec[stf - 1, location, tech]}"
            )
            return (
                m.pricereduction_sec[stf, location, tech]
                >= m.pricereduction_sec[stf - 1, location, tech]
            )


class q_perstep_constraint_sec(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        """
        Enforces a per-step rule constraint for secondary use capacities for a specific
        location and technology in a given year.

        The constraint ensures that the cumulative sum of capacities (LHS) up to the
        specified year meets or exceeds the calculated requirement based on selected
        steps (RHS). Debugging information is included to confirm the correctness of
        indices and computation values.

        Args:
            m: The model object containing system parameters and constraints.
            stf: The time step
            location: The location under consideration for secondary use.
            tech: The technology under consideration for secondary use.

        Returns:
            bool: True if the constraint is satisfied, False otherwise.
        """
        lhs_cumulative_sum_sec = 0  # Reset LHS for each year
        rhs_value_sec = 0  # Reset RHS for each year

        # Debugging: Check if the indices are correct
        print(
            f"Running q_perstep_rule_sec for stf={stf}, location={location}, tech={tech}"
        )

        # Update cumulative sum for LHS (only for the current year)
        for year in m.stf:
            if year <= stf:  # Accumulate up to the current year (stf)
                try:
                    lhs_cumulative_sum_sec += m.capacity_ext_eusecondary[
                        year, location, tech
                    ]
                except KeyError:
                    print(
                        f"KeyError: capacity_ext_eusecondary[{year}, {location}, {tech}]"
                    )
                    raise

        # Calculate RHS based on selected stages (only for the current year)
        rhs_value_sec = sum(
            m.BD_sec[stf, location, tech, n] * m.capacityperstep_sec[n, location, tech]
            for n in m.nsteps_sec
        )

        # Debug: Print LHS and selected RHS value for each year
        print(
            f"Step {stf}: LHS cumulative sum = {lhs_cumulative_sum_sec}, RHS value = {rhs_value_sec}"
        )

        # Return the constraint for this specific year
        return lhs_cumulative_sum_sec >= rhs_value_sec


def apply_rm1_constraints(m):
    constraints = [
        costsavings_constraint_sec(),
        BD_limitation_constraint_sec(),
        relation_pnew_to_pprior_constraint_sec(),
        q_perstep_constraint_sec()
    ]

    for i, constraint in enumerate(constraints):
        constraint_name = f"constraint_{i + 1}"
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
