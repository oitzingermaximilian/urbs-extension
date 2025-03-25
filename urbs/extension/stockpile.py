from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, stf, location, tech):
        pass


class CapacityExtGrowthRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            capacity_extensionpackage = (
                m.capacity_ext[stf, location, tech]
                == m.capacity_ext[stf - 1, location, tech]
                + m.capacity_ext_new[stf, location, tech]
                - m.capacity_dec[stf, location, tech]
            )
            print(
                f"Capacity extension package for {tech} at {location} in year {stf}: {capacity_extensionpackage}"
            )
            return capacity_extensionpackage


class InitialCapacityRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            capacity_eq1 = (
                m.capacity_ext[stf, location, tech]
                == m.Installed_Capacity_Q_s[location, tech]
                + m.capacity_ext_new[stf, location, tech]
                - m.capacity_dec[stf, location, tech]
            )
            print(
                f"Initial Capacity for {tech} at {location} in year {stf}: {capacity_eq1}"
            )
            return capacity_eq1
        else:
            return pyomo.Constraint.Skip


class CapacityExtNewRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        capacity_eq2 = m.capacity_ext_new[stf, location, tech] == (
            m.capacity_ext_imported[stf, location, tech]
            + m.capacity_ext_stockout[stf, location, tech]
            + m.capacity_ext_euprimary[stf, location, tech]
            + m.capacity_ext_eusecondary[stf, location, tech]
        )
        print(
            f"Capacity Extension New for {tech} at {location} in year {stf}: {capacity_eq2}"
        )
        return capacity_eq2


class CapacityExtStockRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            capacity_eq3 = m.capacity_ext_stock[stf, location, tech] == (
                m.capacity_ext_stock[stf - 1, location, tech]
                + m.capacity_ext_stock_imported[stf, location, tech]
                - m.capacity_ext_stockout[stf, location, tech]
            )
            print(
                f"Capacity Extension Stock for {tech} at {location} in year {stf}: {capacity_eq3}"
            )
            return capacity_eq3


class CapacityExtStockInitialRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            capacity_eq4 = m.capacity_ext_stock[stf, location, tech] == (
                m.Existing_Stock_Q_stock[location, tech]
                + m.capacity_ext_stock_imported[stf, location, tech]
                - m.capacity_ext_stockout[stf, location, tech]
            )
            print(
                f"Capacity Extension Stock Initial for {tech} at {location} in year {stf}: {capacity_eq4}"
            )
            return capacity_eq4
        else:
            return pyomo.Constraint.Skip


class StockTurnoverRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        valid_years = [2025, 2030, 2035, 2040, 2045]

        if stf in valid_years:
            lhs = sum(
                m.capacity_ext_stockout[j, location, tech]
                for j in range(stf, stf + m.n)
                if j in m.capacity_ext_stockout
            )
            print(f"LHS for {tech} at {location} in year {stf}: {lhs}")

            rhs = (
                m.FT
                * (1 / m.n)
                * sum(
                    m.capacity_ext_stock[j, location, tech]
                    for j in range(stf, stf + m.n)
                    if j in m.capacity_ext_stock
                )
            )
            print(f"RHS for {tech} at {location} in year {stf}: {rhs}")

            return lhs >= rhs
        else:
            return pyomo.Constraint.Skip


class AntiDumpingMeasuresRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        rhs = m.anti_dumping_index[location, tech] * (
            m.capacity_ext_imported[stf, location, tech]
            + m.capacity_ext_stock_imported[stf, location, tech]
        )

        print(
            f"Anti-Dumping Measure for {tech} at {location} in year {stf}: "
            f"{m.anti_dumping_measures[stf, location, tech]} = {rhs}"
        )

        return m.anti_dumping_measures[stf, location, tech] == rhs


class CapacityExtNewLimitRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        capacity_value = m.capacity_ext_new[stf, location, tech]
        ext_new_value = m.Q_ext_new[stf, location, tech]

        print(
            f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, Capacity Solar New = {capacity_value}, max installable Capacity = {ext_new_value}"
        )

        return capacity_value <= ext_new_value


class TimedelayEUPrimaryProductionRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            lhs = (
                m.capacity_ext_euprimary[stf, location, tech]
                - m.capacity_ext_euprimary[stf - 1, location, tech]
            )
            rhs = (
                m.deltaQ_EUprimary[location, tech]
                + m.IR_EU_primary[location, tech]
                * m.capacity_ext_euprimary[stf - 1, location, tech]
            )

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs


class TimedelayEUSecondaryProductionRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            lhs = (
                m.capacity_ext_eusecondary[stf, location, tech]
                - m.capacity_ext_eusecondary[stf - 1, location, tech]
            )
            rhs = (
                m.deltaQ_EUsecondary[location, tech]
                + m.IR_EU_secondary[location, tech]
                * m.capacity_ext_eusecondary[stf - 1, location, tech]
            )

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs


class Constraint1EUSecondaryToTotalRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        l_value = m.l[location, tech]
        if m.y0 <= stf - l_value:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = m.capacity_ext_new[stf - l_value, location, tech]

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs
        else:
            return pyomo.Constraint.Skip


class Constraint2EUSecondaryToTotalRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        l_value = m.l[location, tech]
        if m.y0 >= stf - l_value:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = m.DCR_solar[stf, location, tech] * m.capacity_ext[stf, location, tech]

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs <= rhs
        else:
            return pyomo.Constraint.Skip


class ConstraintEUPrimaryToTotalRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            lhs = m.capacity_ext_euprimary[stf, location, tech]
            rhs = (
                m.DR_primary[location, tech]
                * m.capacity_ext_euprimary[stf - 1, location, tech]
            )

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs >= rhs


class ConstraintEUSecondaryToSecondaryRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        if stf == m.y0:
            return pyomo.Constraint.Skip
        else:
            lhs = m.capacity_ext_eusecondary[stf, location, tech]
            rhs = (
                m.DR_secondary[location, tech]
                * m.capacity_ext_eusecondary[stf - 1, location, tech]
            )

            print(
                f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
            )

            return lhs >= rhs


class ConstraintMaxIntoStockRule(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        # Calculate the left-hand side (LHS) and right-hand side (RHS)
        lhs = m.capacity_ext_stock_imported[stf, location, tech]
        rhs = 0.5 * m.capacity_ext_imported[stf, location, tech]

        # Debugging: Print the LHS and RHS values
        print(
            f"Debug: STF = {stf}, Location = {location}, Tech = {tech}, LHS = {lhs}, RHS = {rhs}"
        )

        return lhs <= rhs


def apply_stockpiling_constraints(m):
    constraints = [
        CapacityExtGrowthRule(),
        InitialCapacityRule(),
        CapacityExtNewRule(),
        CapacityExtStockRule(),
        CapacityExtStockInitialRule(),
        # StockTurnoverRule(),
        AntiDumpingMeasuresRule(),
        CapacityExtNewLimitRule(),
        TimedelayEUPrimaryProductionRule(),
        TimedelayEUSecondaryProductionRule(),
        # Constraint1EUSecondaryToTotalRule(), #ToDo fix this constraint
        Constraint2EUSecondaryToTotalRule(),
        ConstraintEUPrimaryToTotalRule(),
        ConstraintEUSecondaryToSecondaryRule(),
        ConstraintMaxIntoStockRule(),
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
