from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, stf, location, tech):
        pass


DEBUG = False  # flip to True to enable cost‐constraint logging


def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


class DefCostsNew(AbstractConstraint):
    def apply_rule(self, m, cost_type_new):
        if cost_type_new == "Importcost":
            total_import_cost = sum(
                (
                    m.IMPORTCOST[stf, site, tech]
                    * (
                        m.capacity_ext_imported[stf, site, tech]
                        + m.capacity_ext_stock_imported[stf, site, tech]
                    )
                )
                + (
                    m.capacity_ext_stock_imported[stf, site, tech]
                    * m.logisticcost[site, tech]
                )
                + m.anti_dumping_measures[stf, site, tech]
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )
            expr = m.costs_new[cost_type_new] == total_import_cost
            debug_print(
                f"[DefCostsNew-Import] total_import_cost = {total_import_cost}\n"
                f"    expr: {expr}"
            )
            return expr

        elif cost_type_new == "Storagecost":
            total_storage_cost = sum(
                m.STORAGECOST[site, tech] * m.capacity_ext_stock[stf, site, tech]
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )
            expr = m.costs_new[cost_type_new] == total_storage_cost
            debug_print(
                f"[DefCostsNew-Storage] total_storage_cost = {total_storage_cost}\n"
                f"    expr: {expr}"
            )
            return expr

        elif cost_type_new == "Eu Cost Primary":
            total_eu_cost_primary = sum(
                m.EU_primary_costs[stf, site, tech]
                * m.capacity_ext_euprimary[stf, site, tech]
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )
            expr = m.costs_new[cost_type_new] == total_eu_cost_primary
            debug_print(
                f"[DefCostsNew-EU Primary] total_eu_cost_primary = {total_eu_cost_primary}\n"
                f"    expr: {expr}"
            )
            return expr

        elif cost_type_new == "Eu Cost Secondary":
            total_eu_cost_secondary = sum(
                (
                    (
                        m.EU_secondary_costs[stf, site, tech]
                        - m.pricereduction_sec[stf, site, tech]
                    )
                    * m.capacity_ext_eusecondary[stf, site, tech]
                    + m.cost_scrap[stf, site, tech]
                )
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )
            expr = m.costs_new[cost_type_new] == total_eu_cost_secondary
            debug_print(
                f"[DefCostsNew-EU Secondary] total_eu_cost_secondary = {total_eu_cost_secondary}\n"
                f"    expr: {expr}"
            )
            return expr

        else:
            raise NotImplementedError(f"Unknown cost type: {cost_type_new}")


class CalculateYearlyImportCost(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        import_cost_value = (
            m.IMPORTCOST[stf, location, tech]
            * (
                m.capacity_ext_imported[stf, location, tech]
                + m.capacity_ext_stock_imported[stf, location, tech]
            )
            + (
                m.capacity_ext_stock_imported[stf, location, tech]
                * m.logisticcost[location, tech]
            )
            + m.anti_dumping_measures[stf, location, tech]
        )
        expr = m.costs_ext_import[stf, location, tech] == import_cost_value
        debug_print(
            f"[YearlyImport] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"import_cost_value={import_cost_value}\n    expr: {expr}"
        )
        return expr


class CalculateYearlyStorageCost(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        storage_cost_value = (
            m.STORAGECOST[location, tech] * m.capacity_ext_stock[stf, location, tech]
        )
        expr = m.costs_ext_storage[stf, location, tech] == storage_cost_value
        debug_print(
            f"[YearlyStorage] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"storage_cost_value={storage_cost_value}\n    expr: {expr}"
        )
        return expr


class CalculateYearlyEUPrimary(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        eu_primary_cost_value = (
            m.EU_primary_costs[stf, location, tech]
            * m.capacity_ext_euprimary[stf, location, tech]
        )
        expr = m.costs_EU_primary[stf, location, tech] == eu_primary_cost_value
        debug_print(
            f"[YearlyEUPrimary] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"eu_primary_cost_value={eu_primary_cost_value}\n    expr: {expr}"
        )
        return expr


class CalculateYearlyEUSecondary(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        eu_secondary_cost_value = (
            m.EU_secondary_costs[stf, location, tech]
            - m.pricereduction_sec[stf, location, tech]
        ) * m.capacity_ext_eusecondary[stf, location, tech] + m.cost_scrap[
            stf, location, tech
        ]
        expr = m.costs_EU_secondary[stf, location, tech] == eu_secondary_cost_value
        debug_print(
            f"[YearlyEUSecondary] STF={stf}, loc={location}, tech={tech}  ➞ "
            f"eu_secondary_cost_value={eu_secondary_cost_value}\n    expr: {expr}"
        )
        return expr


def apply_costs_constraints(m):
    constraints = [
        CalculateYearlyImportCost(),
        CalculateYearlyStorageCost(),
        CalculateYearlyEUPrimary(),
        CalculateYearlyEUSecondary(),
    ]

    for i, constraint in enumerate(constraints):
        constraint_name = f"yearly_cost_constraint_{i + 1}"
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

    # Apply the def_costs_new constraint separately as it uses cost_type_new
    setattr(
        m,
        "cost_constraint_new",
        pyomo.Constraint(
            m.cost_type_new,
            rule=lambda m, cost_type_new: DefCostsNew().apply_rule(m, cost_type_new),
        ),
    )
