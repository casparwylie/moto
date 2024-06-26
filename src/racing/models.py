from pydantic import BaseModel
from sqlalchemy import Row


class SuccessResponse(BaseModel):
    success: bool
    errors: list[str] = []


class Racer(BaseModel):
    model_id: int
    name: str | None
    full_name: str | None
    make_name: str | None
    style: str | None
    year: str | None
    power: str | None
    torque: str | None
    weight: str | None
    weight_type: str | None

    @classmethod
    def from_db_data(cls, data: Row) -> "Racer":
        return cls(
            model_id=data.id,
            full_name=f"{data.make_name} {data.name}",
            make_name=data.make_name,
            name=data.name,
            style=data.style,
            year=data.year,
            power=data.power,
            torque=data.torque,
            weight=data.weight,
            weight_type=data.weight_type,
        )


class SaveRequest(BaseModel):
    model_ids: list[int]


class Race(BaseModel):
    race_id: int
    racers: list[Racer]
    user_id: int | None = None
    race_unique_id: str

    @classmethod
    def from_service(cls, race: Row, racers: list[Row]) -> "Race":
        return cls(
            race_id=race.id,
            racers=[Racer.from_db_data(racer_data) for racer_data in racers],
            user_id=race.user_id,
            race_unique_id=race.race_unique_id,
        )


class RaceListing(BaseModel):
    races: list[Race]

    @classmethod
    def from_service(
        cls, races_and_racers: list[tuple[None | Row, list[Row]]]
    ) -> "RaceListing":
        return cls(
            races=[
                Race.from_service(race, racers)
                for race, racers in races_and_racers
                if race and racers
            ]
        )


class RaceVotesResponse(BaseModel):
    upvotes: int
    downvotes: int


class RaceVoteRequest(BaseModel):
    race_unique_id: str
    vote: int


class HasVotedResponse(BaseModel):
    voted: bool


class MakesSearchResponse(BaseModel):
    makes: list[str]
