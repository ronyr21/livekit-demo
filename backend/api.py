from livekit.agents import Agent, function_tool, RunContext
import enum
from typing import Optional
import logging
from db_driver import DatabaseDriver

logger = logging.getLogger("user-data")
logger.setLevel(logging.INFO)

DB = DatabaseDriver()


class CarDetails(enum.Enum):
    VIN = "vin"
    Make = "make"
    Model = "model"
    Year = "year"


class AssistantFnc(Agent):
    def __init__(self, instructions: str):
        super().__init__(instructions=instructions)
        self._car_details = {
            CarDetails.VIN: "",
            CarDetails.Make: "",
            CarDetails.Model: "",
            CarDetails.Year: "",
        }

    def get_car_str(self):
        car_str = ""
        for key, value in self._car_details.items():
            car_str += f"{key}: {value}\n"
        return car_str

    @function_tool
    async def lookup_car(self, ctx: RunContext, vin: str) -> str:
        """
        Lookup a car by its VIN.

        Parameters:
        vin (str): The VIN of the car to lookup.
        """
        logger.info("lookup car - vin: %s", vin)
        result = DB.get_car_by_vin(vin)
        if result is None:
            return "Car not found"
        self._car_details = {
            CarDetails.VIN: result.vin,
            CarDetails.Make: result.make,
            CarDetails.Model: result.model,
            CarDetails.Year: result.year,
        }
        return f"The car details are: {self.get_car_str()}"

    @function_tool
    async def get_car_details(self, ctx: RunContext) -> str:
        """
        Get the details of the current car.
        """
        logger.info("get car details")
        return f"The car details are: {self.get_car_str()}"

    @function_tool
    async def create_car(
        self, ctx: RunContext, vin: str, make: str, model: str, year: int
    ) -> str:
        """
        Create a new car.

        Parameters:
        vin (str): The VIN of the car.
        make (str): The make of the car.
        model (str): The model of the car.
        year (int): The year of the car.
        """
        logger.info(
            "create car - vin: %s, make: %s, model: %s, year: %s",
            vin,
            make,
            model,
            year,
        )
        result = DB.create_car(vin, make, model, year)
        if result is None:
            return "Failed to create car"
        self._car_details = {
            CarDetails.VIN: result.vin,
            CarDetails.Make: result.make,
            CarDetails.Model: result.model,
            CarDetails.Year: result.year,
        }
        return "Car created!"

    def has_car(self) -> bool:
        return self._car_details[CarDetails.VIN] != ""
