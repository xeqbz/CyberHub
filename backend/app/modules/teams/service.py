from app.modules.teams.model import Team, TeamMember, TeamMemberRole
from app.modules.teams.repository import TeamRepository
from app.modules.teams.schemas import TeamCreate, TeamUpdate


class TeamError(Exception):
    pass


class TeamNotFoundError(TeamError):
    pass


class TeamAlreadyExistsError(TeamError):
    pass


class TeamAccessDeniedError(TeamError):
    pass


class TeamMemberAlreadyExistsError(TeamError):
    pass


class TeamMemberNotFoundError(TeamError):
    pass


class TeamOwnerRemovalError(TeamError):
    pass


class TeamOwnerRoleChangeError(TeamError):
    pass


class TeamService:
    def __init__(self, repository: TeamRepository) -> None:
        self.repository = repository

    def get_team_by_id(self, team_id: int) -> Team | None:
        return self.repository.get_by_id(team_id)

    def get_team_or_raise(self, team_id: int) -> Team:
        team = self.repository.get_by_id(team_id)
        if team is None:
            raise TeamNotFoundError("Team not found")
        return team

    def get_team_by_name(self, name: str) -> Team | None:
        return self.repository.get_by_name(name.strip())

    def list_teams(self, offset: int = 0, limit: int = 100) -> list[Team]:
        return self.repository.list_teams(offset=offset, limit=limit)

    def list_user_teams(self, user_id: int) -> list[Team]:
        teams = self.repository.list_by_member(user_id)

        unique_teams: list[Team] = []
        seen_ids: set[int] = set()

        for team in teams:
            if team.id not in seen_ids:
                seen_ids.add(team.id)
                unique_teams.append(team)

        return unique_teams

    def create_team(self, data: TeamCreate, owner_id: int) -> Team:
        normalized_name = data.name.strip()

        existing_team = self.repository.get_by_name(normalized_name)
        if existing_team is not None:
            raise TeamAlreadyExistsError("Team with this name already exists")

        team = self.repository.create(
            name=normalized_name,
            description=data.description,
            owner_id=owner_id,
        )

        self.repository.add_member(
            team_id=team.id,
            user_id=owner_id,
            role=TeamMemberRole.OWNER,
        )

        return self.get_team_or_raise(team.id)

    def update_team(
        self,
        team_id: int,
        acting_user_id: int,
        data: TeamUpdate,
    ) -> Team:
        team = self.get_team_or_raise(team_id)
        self._ensure_owner_access(team, acting_user_id)

        normalized_name = data.name.strip() if data.name is not None else None

        if normalized_name is not None and normalized_name != team.name:
            existing_team = self.repository.get_by_name(normalized_name)
            if existing_team is not None and existing_team.id != team.id:
                raise TeamAlreadyExistsError("Team with this name already exists")

        updated_team = self.repository.update(
            team,
            name=normalized_name,
            description=data.description,
        )

        return self.get_team_or_raise(updated_team.id)

    def delete_team(self, team_id: int, acting_user_id: int) -> None:
        team = self.get_team_or_raise(team_id)
        self._ensure_owner_access(team, acting_user_id)
        self.repository.delete(team)

    def add_member(
        self,
        team_id: int,
        acting_user_id: int,
        user_id: int,
        role: TeamMemberRole = TeamMemberRole.MEMBER,
    ) -> TeamMember:
        team = self.get_team_or_raise(team_id)
        self._ensure_owner_access(team, acting_user_id)

        existing_member = self.repository.get_member(team_id=team.id, user_id=user_id)
        if existing_member is not None:
            raise TeamMemberAlreadyExistsError("User is already a team member")

        return self.repository.add_member(
            team_id=team.id,
            user_id=user_id,
            role=role,
        )

    def remove_member(
        self,
        team_id: int,
        acting_user_id: int,
        user_id: int,
    ) -> None:
        team = self.get_team_or_raise(team_id)
        self._ensure_owner_access(team, acting_user_id)

        member = self.repository.get_member(team_id=team.id, user_id=user_id)
        if member is None:
            raise TeamMemberNotFoundError("Team member not found")

        if member.user_id == team.owner_id:
            raise TeamOwnerRemovalError("Team owner cannot be removed")

        self.repository.remove_member(member)

    def update_member_role(
        self,
        team_id: int,
        acting_user_id: int,
        user_id: int,
        role: TeamMemberRole,
    ) -> TeamMember:
        team = self.get_team_or_raise(team_id)
        self._ensure_owner_access(team, acting_user_id)

        member = self.repository.get_member(team_id=team.id, user_id=user_id)
        if member is None:
            raise TeamMemberNotFoundError("Team member not found")

        if member.user_id == team.owner_id and role != TeamMemberRole.OWNER:
            raise TeamOwnerRoleChangeError("Team owner role cannot be changed")

        return self.repository.update_member_role(member, role=role)

    def get_member(self, team_id: int, user_id: int) -> TeamMember | None:
        return self.repository.get_member(team_id=team_id, user_id=user_id)

    def list_members(self, team_id: int) -> list[TeamMember]:
        team = self.get_team_or_raise(team_id)
        return self.repository.list_members(team.id)

    @staticmethod
    def _ensure_owner_access(team: Team, acting_user_id: int) -> None:
        if team.owner_id != acting_user_id:
            raise TeamAccessDeniedError("Only team owner can perform this action")
