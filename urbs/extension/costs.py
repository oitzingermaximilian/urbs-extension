from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, stf, location, tech):
        pass


class DefCostsNew(AbstractConstraint):
    def apply_rule(self, m, cost_type_new):
        if cost_type_new == "Importcost":
            # Calculating total import cost across all time steps, locations, and technologies
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

            #print("Calculating Import Cost Total:")
            #print(f"Total Import Cost = {total_import_cost}")
            return m.costs_new[cost_type_new] == total_import_cost

        elif cost_type_new == "Storagecost":
            # Calculating total storage cost across all time steps and locations/technologies if needed
            total_storage_cost = sum(
                m.STORAGECOST[site, tech] * m.capacity_ext_stock[stf, site, tech]
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )

            #print("Calculating Storage Cost Total:")
            #print(f"Total Storage Cost = {total_storage_cost}")
            return m.costs_new[cost_type_new] == total_storage_cost

        elif cost_type_new == "Eu Cost Primary":
            # Calculating total EU primary cost across all time steps
            total_eu_cost_primary = sum(
                m.EU_primary_costs[stf, site, tech]
                * m.capacity_ext_euprimary[stf, site, tech]
                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )

            #print("Calculating EU Primary Cost Total:")
            #print(f"Total EU Primary Cost = {total_eu_cost_primary}")
            return m.costs_new[cost_type_new] == total_eu_cost_primary

        elif cost_type_new == "Eu Cost Secondary":
            # Calculating total EU secondary cost across all time steps
            total_eu_cost_secondary = sum(
                (
                    (
                        m.EU_secondary_costs[stf, site, tech]
                       #- m.pricereduction_sec[stf, site, tech]
                        + m.cost_scrap[stf, site, tech]
                    )
                    * m.capacity_ext_eusecondary[stf, site, tech]
                )

                for stf in m.stf
                for site in m.location
                for tech in m.tech
            )

            #print("Calculating EU Secondary Cost Total:")
            #print(f"Total EU Secondary Cost = {total_eu_cost_secondary}")
            return m.costs_new[cost_type_new] == total_eu_cost_secondary

        else:
            raise NotImplementedError("Unknown cost type.")


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
        #print(f"Debug: STF = {stf}, Location = {location}, Tech = {tech}")
        #print(f"Total Yearly Import Cost = {import_cost_value}")
        return m.costs_ext_import[stf, location, tech] == import_cost_value


class CalculateYearlyStorageCost(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        storage_cost_value = (
            m.STORAGECOST[location, tech] * m.capacity_ext_stock[stf, location, tech]
        )
        #print(f"Debug: STF = {stf}, Location = {location}, Tech = {tech}")
        #print(f"Total Yearly Storage Cost = {storage_cost_value}")
        return m.costs_ext_storage[stf, location, tech] == storage_cost_value


class CalculateYearlyEUPrimary(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        eu_primary_cost_value = (
            m.EU_primary_costs[stf, location, tech]
            * m.capacity_ext_euprimary[stf, location, tech]
        )
        #print(f"Debug: STF = {stf}, Location = {location}, Tech = {tech}")
        #print(f"Total Yearly EU Primary Cost = {eu_primary_cost_value}")
        return m.costs_EU_primary[stf, location, tech] == eu_primary_cost_value


class CalculateYearlyEUSecondary(AbstractConstraint):
    def apply_rule(self, m, stf, location, tech):
        eu_secondary_cost_value = (
            m.EU_secondary_costs[stf, location, tech]
            #- m.pricereduction_sec[stf, location, tech]
            + m.cost_scrap[stf, location, tech]
        ) * m.capacity_ext_eusecondary[stf, location, tech]
        #print(f"Debug: STF = {stf}, Location = {location}, Tech = {tech}")
        #print(f"Total Yearly EU Secondary Cost = {eu_secondary_cost_value}")
        return m.costs_EU_secondary[stf, location, tech] == eu_secondary_cost_value


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
