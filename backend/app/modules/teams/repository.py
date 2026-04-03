from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.teams.model import Team, TeamMember, TeamMemberRole


class TeamRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, team_id: int) -> Team | None:
        stmt = (
            select(Team)
            .where(Team.id == team_id)
            .options(
                joinedload(Team.owner),
                selectinload(Team.members).joinedload(TeamMember.user),
            )
        )
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Team | None:
        stmt = select(Team).where(Team.name == name)
        return self.db.scalar(stmt)

    def list_teams(self, offset: int = 0, limit: int = 100) -> list[Team]:
        stmt = (
            select(Team)
            .options(joinedload(Team.owner))
            .offset(offset)
            .limit(limit)
            .order_by(Team.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_by_owner(self, owner_id: int) -> list[Team]:
        stmt = (
            select(Team)
            .where(Team.owner_id == owner_id)
            .options(
                joinedload(Team.owner),
                selectinload(Team.members).joinedload(TeamMember.user),
            )
            .order_by(Team.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_by_member(self, user_id: int) -> list[Team]:
        stmt = (
            select(Team)
            .join(Team.members)
            .where(TeamMember.user_id == user_id)
            .options(
                joinedload(Team.owner),
                selectinload(Team.members).joinedload(TeamMember.user),
            )
            .order_by(Team.id)
        )
        return list(self.db.scalars(stmt).unique().all())

    def create(
        self,
        *,
        name: str,
        description: str | None = None,
        owner_id: int,
    ) -> Team:
        team = Team(
            name=name,
            description=description,
            owner_id=owner_id,
        )
        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def update(
        self,
        team: Team,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Team:
        if name is not None:
            team.name = name
        if description is not None:
            team.description = description

        self.db.add(team)
        self.db.commit()
        self.db.refresh(team)
        return team

    def delete(self, team: Team) -> None:
        self.db.delete(team)
        self.db.commit()

    def get_member(self, team_id: int, user_id: int) -> TeamMember | None:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def list_members(self, team_id: int) -> list[TeamMember]:
        stmt = (
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .options(joinedload(TeamMember.user))
            .order_by(TeamMember.id)
        )
        return list(self.db.scalars(stmt).all())

    def add_member(
        self,
        *,
        team_id: int,
        user_id: int,
        role: TeamMemberRole = TeamMemberRole.MEMBER,
    ) -> TeamMember:
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member_role(
        self,
        member: TeamMember,
        *,
        role: TeamMemberRole,
    ) -> TeamMember:
        member.role = role
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, member: TeamMember) -> None:
        self.db.delete(member)
        self.db.commit()
