# Hack112 Project

### A bullet hell game with several enemy types.

* Dodge enemy fire until time runs out.
* There are several levels with them.
* Bushes block weak projectiles.

#### Red - Player:
* controlled by user using arrow keys

#### Black - Chaser:
* chases player, occasionally charges
* damages player on contact

#### Dark Blue - T Chaser:
* Chases player, occasionally charges, also teleports to where there are not chasers
* Like Chaser, damages player on contact

#### Rose - Archer:
* Circles player, occassionally dashes to change position
* Shoots three arrows in player's direction

#### Pink - Weird Archer:
* Circles player, occassionally dashes to change position/
* Shoots three arrows in some direction.

#### Yellow - Vortal:
* Alters the trajectory of arrows.
* Occasionally teleports.

#### Maroon - Rifleman:
* Like an archer, but shoots one super fast arrow in player's direction instead.
* Prefers to keep its distance.

#### Forest Green - Trapper:
* Moves around the screen, fleeing if the player gets too close.
* Lays mines where it goes.
* The mines will explode and damage the player if they are nearby.

#### Lavender - Lancer:
* Circles the player with its lance.
* Will dash towards the player with the lance ocassionally.
* Will harass the player aggressively if the player is too close.

#### Ghost - White:
* Wanders to spots of interest.
* Is invisible most of the time.
* Damages player on contact.

Requires PIL and pygame to run.