from abc import ABC, abstractmethod
import pyomo.core as pyomo


class AbstractConstraint(ABC):
    @abstractmethod
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        pass


class ConvertTotalCapacityToBalance(AbstractConstraint):
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        balance_value = (
            m.capacity_ext[stf, location, tech]
            * m.lf_solar[timesteps_ext, stf, location, tech]
            * m.hours[timesteps_ext]
        )
        #print(
        #    f"Debug: time = {timesteps_ext}, STF = {stf}, Location = {location}, Tech = {tech}"
        #)
        #print(f"Total Capacity to Balance (Solar) = {balance_value}")
        return m.balance_ext[timesteps_ext, stf, location, tech] == balance_value


class ConvertCapacity1Rule(AbstractConstraint):
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        balance_value = (
            m.capacity_ext_imported[stf, location, tech]  # Capacity in MW
            * m.lf_solar[timesteps_ext, stf, location, tech]  # Load factor
            * m.hours[timesteps_ext]  # Duration of the timestep in hours
        )
        #print(
        #    f"Debug:time = {timesteps_ext}, STF = {stf}, Location = {location}, Tech = {tech}"
        #)
        #print(f"Total Balance (Imported Solar) = {balance_value}")
        return m.balance_import_ext[timesteps_ext, stf, location, tech] == balance_value


class ConvertCapacity2Rule(AbstractConstraint):
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        balance_value = (
            m.capacity_ext_stockout[stf, location, tech]
            * m.lf_solar[timesteps_ext, stf, location, tech]
            * m.hours[timesteps_ext]
        )
        #print(
        #    f"Debug:time = {timesteps_ext}, STF = {stf}, Location = {location}, Tech = {tech}"
        #)
        #print(f"Total Balance (Stockout Solar) = {balance_value}")
        return (
            m.balance_outofstock_ext[timesteps_ext, stf, location, tech]
            == balance_value
        )


class ConvertCapacity3Rule(AbstractConstraint):
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        balance_value = (
            m.capacity_ext_euprimary[stf, location, tech]
            * m.lf_solar[timesteps_ext, stf, location, tech]
            * m.hours[timesteps_ext]
        )
        #print(
        #    f"Debug:time = {timesteps_ext}, STF = {stf}, Location = {location}, Tech = {tech}"
        #)
        #print(f"Total Balance (EU Primary Solar) = {balance_value}")
        return (
            m.balance_EU_primary_ext[timesteps_ext, stf, location, tech]
            == balance_value
        )


class ConvertCapacity4Rule(AbstractConstraint):
    def apply_rule(self, m, timesteps_ext, stf, location, tech):
        balance_value = (
            m.capacity_ext_eusecondary[stf, location, tech]
            * m.lf_solar[timesteps_ext, stf, location, tech]
            * m.hours[timesteps_ext]
        )
        #print(
        #    f"Debug:time = {timesteps_ext}, STF = {stf}, Location = {location}, Tech = {tech}"
        #)
        #print(f"Total Balance (EU Secondary Solar) = {balance_value}")
        return (
            m.balance_EU_secondary_ext[timesteps_ext, stf, location, tech]
            == balance_value
        )


def apply_balance_constraints(m):
    constraints = [
        ConvertTotalCapacityToBalance(),
        ConvertCapacity1Rule(),
        ConvertCapacity2Rule(),
        ConvertCapacity3Rule(),
        ConvertCapacity4Rule(),
    ]

    for i, constraint in enumerate(constraints):
        constraint_name = f"balance_constraint_{i + 1}"
        setattr(
            m,
            constraint_name,
            pyomo.Constraint(
                m.timesteps_ext,
                m.stf,
                m.location,
                m.tech,
                rule=lambda m, timesteps_ext, stf, loc, tech: constraint.apply_rule(
                    m, timesteps_ext, stf, loc, tech
                ),
            ),
        )
