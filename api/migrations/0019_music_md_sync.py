"""Every emotion's and every mix's list, exactly as docs/music.md gives it.

The docs/music.md the therapist approved, as saved 2026-11-06 07:44. This sets
each of the twelve emotion lists and the five mix lists to it, in its order
(position 1..n):

* Every emotion list has ten songs and every mix five; the document has no
  repeats left.
* NOSTALGIC has two different songs called "Photograph" (Ed Sheeran,
  Nickelback); they are matched on title and artist, so both stay.
* Songs already in the collection are reused under their stored spelling --
  "Awitin Mo at Isasayaw Ko" is the "Awitin Mo, Isasayaw ko" row, "Merry-Go-
  Round" is "Merry-Go-Round of Life", "Bittersweet" is "bittersweet", and so
  on; each was checked to be the same Spotify track.
* New songs carry the original release, looked up on Spotify by exact title
  and artist. "Zombie" uses No Need To Argue's 2025 remaster, the only studio
  release Spotify still carries. "Surprise" by P!nk is not on Spotify under
  that title and artist, so it is stored without a track (an "Open in
  Spotify" search link, as 0008 did) until the title is confirmed; a later
  migration only has to set its spotify_track_id.
* A song taken out of a list is only unlinked: its Song row stays, because
  favorites and history can point to it.

The MIXED emotion's own list is not in docs/music.md and is left as it is.

Undoing puts every list back to its 0018 state and removes the songs this
added that nothing else uses.
"""
from django.db import migrations

# Songs not yet in the collection.
NEW_SONGS = [
    {'title': 'I Gotta Feeling', 'artist': 'The Black Eyed Peas',
     'spotify_track_id': '2H1047e0oMSj10dgp7p2VG', 'album': 'THE E.N.D. (THE ENERGY NEVER DIES)',
     'image': 'https://i.scdn.co/image/ab67616d0000b273382514f0114ba8f4a16d5db4',
     'duration_ms': 289133},
    {'title': 'Tala', 'artist': 'Sarah Geronimo',
     'spotify_track_id': '6C6F2oA7cmZKqq26FPGl0J', 'album': 'The Great Unknown',
     'image': 'https://i.scdn.co/image/ab67616d0000b273dd6e82e86e2d9afc739966bc',
     'duration_ms': 245053},
    {'title': 'Beautiful Day', 'artist': 'U2',
     'spotify_track_id': '0gzqZ9d1jIKo9psEIthwXe', 'album': "All That You Can't Leave Behind",
     'image': 'https://i.scdn.co/image/ab67616d0000b27338fa0dfe55b1ff2e8c962bae',
     'duration_ms': 248400},
    {'title': 'Saksi Ang Langit', 'artist': 'December Avenue',
     'spotify_track_id': '6tPFZRJKj5JR7qO3qWxaVm', 'album': 'Saksi Ang Langit',
     'image': 'https://i.scdn.co/image/ab67616d0000b2737060277073fc2ae384281296',
     'duration_ms': 259058},
    {'title': 'Pagsuko', 'artist': 'Jireh Lim',
     'spotify_track_id': '04EkY1xc5yYedjagb27ndZ', 'album': 'Love And Soul',
     'image': 'https://i.scdn.co/image/ab67616d0000b273e00864ab4f95a41bb50cf786',
     'duration_ms': 307013},
    {'title': 'Walang Natira', 'artist': 'Gloc-9',
     'spotify_track_id': '21FPqoc0NyXVB3wiB3iFRg', 'album': 'Talumpati',
     'image': 'https://i.scdn.co/image/ab67616d0000b273ce2efccc92a666db5f13d01f',
     'duration_ms': 240040},
    {'title': 'Before He Cheats', 'artist': 'Carrie Underwood',
     'spotify_track_id': '0ZUo4YjG4saFnEJhdWp9Bt', 'album': 'Some Hearts',
     'image': 'https://i.scdn.co/image/ab67616d0000b273c20ffeb64e39773de0f6c232',
     'duration_ms': 199939},
    {'title': 'Since U Been Gone', 'artist': 'Kelly Clarkson',
     'spotify_track_id': '6JY1IdkZGeIcPegKxjSKeb', 'album': 'Breakaway',
     'image': 'https://i.scdn.co/image/ab67616d0000b273158c72ad0003cb37ca0c9eff',
     'duration_ms': 188960},
    {'title': 'Rise Up', 'artist': 'Andra Day',
     'spotify_track_id': '0tV8pOpiNsKqUys0ilUcXz', 'album': 'Cheers to the Fall',
     'image': 'https://i.scdn.co/image/ab67616d0000b273ccd9af18cc83991382c9ab9a',
     'duration_ms': 253342},
    {'title': 'Titanium', 'artist': 'David Guetta ft. Sia',
     'spotify_track_id': '0TDLuuLlV54CkRRUOahJb4', 'album': 'Nothing but the Beat (Ultimate Edition)',
     'image': 'https://i.scdn.co/image/ab67616d0000b27363bf1cd36632031eb3081cb0',
     'duration_ms': 245040},
    {'title': 'Liwanag sa Dilim', 'artist': 'Rivermaya',
     'spotify_track_id': '5bDKiU0VIsv80ejRRKcYN2', 'album': 'Rivermaya Silver Series',
     'image': 'https://i.scdn.co/image/ab67616d0000b273f9ba49345581a957265310d7',
     'duration_ms': 219786},
    {'title': "Everybody's Fool", 'artist': 'Evanescence',
     'spotify_track_id': '0tWEB6BxbI48XN79QE1JbT', 'album': 'Fallen',
     'image': 'https://i.scdn.co/image/ab67616d0000b27325f49ab23f0ec6332efef432',
     'duration_ms': 195880},
    {'title': 'Disturbia', 'artist': 'Rihanna',
     'spotify_track_id': '2VOomzT6VavJOGBeySqaMc', 'album': 'Good Girl Gone Bad: Reloaded',
     'image': 'https://i.scdn.co/image/ab67616d0000b273f9f27162ab1ed45b8d7a7e98',
     'duration_ms': 238626},
    {'title': 'Zombie', 'artist': 'The Cranberries',
     'spotify_track_id': '3gjHnylel3PTRpjS44ocqr', 'album': 'No Need To Argue (2025 Remastered)',
     'image': 'https://i.scdn.co/image/ab67616d0000b27320a28883cdd0fc7d5f85a9a9',
     'duration_ms': 305626},
    {'title': 'Monster', 'artist': 'Imagine Dragons',
     'spotify_track_id': '4uyDe8SeM0Nsgzp9KMtXWn', 'album': 'Smoke + Mirrors (Deluxe)',
     'image': 'https://i.scdn.co/image/ab67616d0000b27359ac0a9acb7bf0d315301152',
     'duration_ms': 250506},
    {'title': 'Control', 'artist': 'Halsey',
     'spotify_track_id': '3SKzTIl9mW0DadTys9SFo3', 'album': 'BADLANDS (Deluxe)',
     'image': 'https://i.scdn.co/image/ab67616d0000b27374fefed78db6d6cf4d963fdc',
     'duration_ms': 214761},
    {'title': 'Numb', 'artist': 'Linkin Park',
     'spotify_track_id': '2nLtzopw4rPReszdYBJU6h', 'album': 'Meteora',
     'image': 'https://i.scdn.co/image/ab67616d0000b2735f1f51d14e8bea89484ecd1b',
     'duration_ms': 187520},
    {'title': 'Hurt', 'artist': 'Johnny Cash',
     'spotify_track_id': '28cnXtME493VX9NOw9cIUh', 'album': 'American IV: The Man Comes Around',
     'image': 'https://i.scdn.co/image/ab67616d0000b2736f4f62da3d811b6501a69ffa',
     'duration_ms': 216533},
    {'title': 'How to Save a Life', 'artist': 'The Fray',
     'spotify_track_id': '5fVZC9GiM4e8vu99W0Xf6J', 'album': 'How To Save A Life',
     'image': 'https://i.scdn.co/image/ab67616d0000b27359b8b957f164ce660919f1f4',
     'duration_ms': 262533},
    {'title': 'Everybody Hurts', 'artist': 'R.E.M.',
     'spotify_track_id': '6PypGyiu0Y2lCDBN1XZEnP', 'album': 'Automatic For The People',
     'image': 'https://i.scdn.co/image/ab67616d0000b273ace3e7aae0b7c78bbe1c4f35',
     'duration_ms': 320266},
    {'title': 'Heavy', 'artist': 'Linkin Park ft. Kiiara',
     'spotify_track_id': '104buTcnP2AsxqB7U1FIZ4', 'album': 'One More Light',
     'image': 'https://i.scdn.co/image/ab67616d0000b273145e1cf12538f5666511237d',
     'duration_ms': 169800},
    {'title': 'Innocence', 'artist': 'Hildir Svensson and deprezz',
     'spotify_track_id': '3rv58nZ7Pk3PB9lTIujQFi', 'album': 'Innocence',
     'image': 'https://i.scdn.co/image/ab67616d0000b2737be6a7a5535a936f511cf988',
     'duration_ms': 356639},
    {'title': 'Breathe Me', 'artist': 'Sia',
     'spotify_track_id': '7jqzZyJJLrpkRFYGpkqSK6', 'album': 'Colour The Small One',
     'image': 'https://i.scdn.co/image/ab67616d0000b273940e6dd89f311e726fb5687c',
     'duration_ms': 272800},
    {'title': 'Photograph', 'artist': 'Nickelback',
     'spotify_track_id': '3hb2ScEVkGchcAQqrPLP0R', 'album': 'All the Right Reasons',
     'image': 'https://i.scdn.co/image/ab67616d0000b27307fb7d8037f3962394c493ca',
     'duration_ms': 258920},
    {'title': 'See You Again', 'artist': 'Wiz Khalifa ft. Charlie Puth',
     'spotify_track_id': '4Aep3WGBQlpbKXkW7kfqcU', 'album': 'Furious 7: Original Motion Picture Soundtrack',
     'image': 'https://i.scdn.co/image/ab67616d0000b273658f35df0da6f9393a501fbf',
     'duration_ms': 229525},
    {'title': 'When We Were Young', 'artist': 'Adele',
     'spotify_track_id': '6O5TrlFWTYvznd9fMC0VvU', 'album': '25',
     'image': 'https://i.scdn.co/image/ab67616d0000b2737b9888dc365b8f957c63df14',
     'duration_ms': 290900},
    {'title': 'Marilag', 'artist': 'Dionela',
     'spotify_track_id': '2zbq6eS68i4NIJWekIuW1s', 'album': 'Marilag',
     'image': 'https://i.scdn.co/image/ab67616d0000b2734fac68d7fc631af679325118',
     'duration_ms': 157692},
    {'title': 'Lonely', 'artist': 'Akon',
     'spotify_track_id': '6ls5ulRydoPE7oWGPGBqFA', 'album': 'Trouble',
     'image': 'https://i.scdn.co/image/ab67616d0000b27375efdb59b1ab02452a7d59e0',
     'duration_ms': 235066},
    {'title': 'Bloom', 'artist': 'The Paper Kites',
     'spotify_track_id': '1HMQmOWrkieKYWlFsjUP3D', 'album': 'Woodland',
     'image': 'https://i.scdn.co/image/ab67616d0000b27355bd9d9e0f50d28ddc9c1308',
     'duration_ms': 210080},
    {'title': 'Breathin', 'artist': 'Ariana Grande',
     'spotify_track_id': '4OafepJy2teCjYJbvFE60J', 'album': 'Sweetener',
     'image': 'https://i.scdn.co/image/ab67616d0000b273c3af0c2355c24ed7023cd394',
     'duration_ms': 198160},
    {'title': 'Anxiety', 'artist': 'Julia Michaels ft. Selena Gomez',
     'spotify_track_id': '1XJ93XskwJf7PCyIVLbNBt', 'album': 'Inner Monologue Part 1',
     'image': 'https://i.scdn.co/image/ab67616d0000b2737e706949994bcef39b09da4e',
     'duration_ms': 210146},
    {'title': 'In the End', 'artist': 'Linkin Park',
     'spotify_track_id': '7q115ia4fQn9zonjpexWsY', 'album': 'Hybrid Theory',
     'image': 'https://i.scdn.co/image/ab67616d0000b2732cd7568f8895a3c031c2e2fb',
     'duration_ms': 216880},
    {'title': 'Everything I Wanted', 'artist': 'Billie Eilish',
     'spotify_track_id': '3ZCTVFBt2Brf31RLEnCkWJ', 'album': 'everything i wanted',
     'image': 'https://i.scdn.co/image/ab67616d0000b273f2248cf6dad1d6c062587249',
     'duration_ms': 245425},
    {'title': 'Surprise', 'artist': 'P!nk',
     'spotify_track_id': None, 'album': '', 'image': '', 'duration_ms': 0},
    {'title': 'Suddenly I See', 'artist': 'KT Tunstall',
     'spotify_track_id': '5p9XWUdvbUzmPCukOmwoU3', 'album': 'Eye To The Telescope',
     'image': 'https://i.scdn.co/image/ab67616d0000b273183730e8038fa632b2c227da',
     'duration_ms': 201706},
    {'title': 'Yellow', 'artist': 'Coldplay',
     'spotify_track_id': '3AJwUDP919kvQ9QcozQPxg', 'album': 'Parachutes',
     'image': 'https://i.scdn.co/image/ab67616d0000b2739164bafe9aaa168d93f4816a',
     'duration_ms': 266773},
    {'title': 'A Sky Full of Stars', 'artist': 'Coldplay',
     'spotify_track_id': '0FDzzruyVECATHXKHFs9eJ', 'album': 'Ghost Stories',
     'image': 'https://i.scdn.co/image/ab67616d0000b273e5a95573f1b91234630fd2cf',
     'duration_ms': 267866},
    {'title': "You'll Be Safe Here", 'artist': 'Rico Blanco',
     'spotify_track_id': '0IuKNTVgn9vapnGU44natX', 'album': "You'll Be Safe Here",
     'image': 'https://i.scdn.co/image/ab67616d0000b2734b582e1cedf6bb25cf3f922b',
     'duration_ms': 304000},
    {'title': 'Banana Pancakes', 'artist': 'Jack Johnson',
     'spotify_track_id': '0BgbobvykXxEvxo2HhCuvM', 'album': 'In Between Dreams',
     'image': 'https://i.scdn.co/image/ab67616d0000b273628dba01c669d89586967dc5',
     'duration_ms': 191906},
    {'title': 'Saturn', 'artist': 'SZA',
     'spotify_track_id': '1bjeWoagtHmUKputLVyDxQ', 'album': 'Saturn',
     'image': 'https://i.scdn.co/image/ab67616d0000b273358f9708c2cc44b153577238',
     'duration_ms': 186191},
    {'title': 'The Greatest Show', 'artist': 'Hugh Jackman & The Greatest Showman Ensemble',
     'spotify_track_id': '4ylWMuGbMXNDgDd8lErEle', 'album': 'The Greatest Showman (Original Motion Picture Soundtrack)',
     'image': 'https://i.scdn.co/image/ab67616d0000b273128057b40732c042c86de1dd',
     'duration_ms': 302146},
    {'title': 'Awit ng Barkada', 'artist': 'APO Hiking Society',
     'spotify_track_id': '6kdiYVZKDNnaFGvIZE5NLQ', 'album': 'Mga Kuwento Ng Apo',
     'image': 'https://i.scdn.co/image/ab67616d0000b2738406c265d884001bf40f0f0f',
     'duration_ms': 217866},
    {'title': "Summer of '69", 'artist': 'Bryan Adams',
     'spotify_track_id': '2jTeyMO0KmMOhKzkAvrnLI', 'album': 'Reckless',
     'image': 'https://i.scdn.co/image/ab67616d0000b273578899f03bd912e82ad531e7',
     'duration_ms': 216597},
    {'title': 'Good Old Days', 'artist': 'Macklemore ft. Kesha',
     'spotify_track_id': '2Za1AlJNvksouPPWbXpR2X', 'album': 'GEMINI',
     'image': 'https://i.scdn.co/image/ab67616d0000b2732e94b668c60b06deb1c3a05c',
     'duration_ms': 240506},]

# Each list in the therapist's order (position 1..n).
EMOTION_SONGS = {
    'happy': [
        ('Happy', 'Pharrell Williams'),
        ("Can't Stop the Feeling!", 'Justin Timberlake'),
        ('Best Day of My Life', 'American Authors'),
        ('I Gotta Feeling', 'The Black Eyed Peas'),
        ('Tala', 'Sarah Geronimo'),
        ('Walking On Sunshine', 'Katrina & The Waves'),
        ('Awitin Mo, Isasayaw ko', 'VST & Company'),
        ('Beautiful Day', 'U2'),
        ("Don't Stop Me Now", 'Queen'),
        ('Ligaya', 'Eraserheads'),
    ],
    'sad': [
        ('Fix You', 'Coldplay'),
        ('Before It Sinks In', 'Moira Dela Torre'),
        ('Happier', 'Ed Sheeran'),
        ('The Night We Met', 'Lord Huron'),
        ('12:51', 'Krissy & Ericka'),
        ('Huling Sandali', 'December Avenue'),
        ('Saksi Ang Langit', 'December Avenue'),
        ('Let Her Go', 'Passenger'),
        ('Pagsuko', 'Jireh Lim'),
        ('Paubaya', 'Moira Dela Torre'),
    ],
    'angry': [
        ('21 Guns', 'Green Day'),
        ('Look What You Made Me Do', 'Taylor Swift'),
        ('Nosi Ba Lasi', 'Sampaguita'),
        ('Walang Natira', 'Gloc-9'),
        ('ERE', 'Juan Karlos'),
        ('You Oughta Know', 'Alanis Morissette'),
        ('Before He Cheats', 'Carrie Underwood'),
        ('Since U Been Gone', 'Kelly Clarkson'),
        ('Upuan', 'Gloc-9'),
        ('Tatsulok', 'Bamboo'),
    ],
    'motivational': [
        ('The Climb', 'Miley Cyrus'),
        ('I Will Survive', 'Demi Lovato'),
        ('Roar', 'Katy Perry'),
        ('Rise Up', 'Andra Day'),
        ('Unstoppable', 'Sia'),
        ('Titanium', 'David Guetta ft. Sia'),
        ('Fight Song', 'Rachel Platten'),
        ('Liwanag sa Dilim', 'Rivermaya'),
        ('Hall of Fame', 'The Script ft. will.i.am'),
        ('Believer', 'Imagine Dragons'),
    ],
    'fear': [
        ("Everybody's Fool", 'Evanescence'),
        ('Creep', 'Radiohead'),
        ("Somebody's Watching Me", 'Rockwell'),
        ('Disturbia', 'Rihanna'),
        ('Zombie', 'The Cranberries'),
        ('Monster', 'Imagine Dragons'),
        ("I'm Scared", 'Young Thug'),
        ('Control', 'Halsey'),
        ('Numb', 'Linkin Park'),
        ('Huwag Kang Matakot', 'Reese Lansangan'),
    ],
    'depressing': [
        ('Hurt', 'Johnny Cash'),
        ('How to Save a Life', 'The Fray'),
        ('Somebody Else', 'The 1975'),
        ('Everybody Hurts', 'R.E.M.'),
        ('Pahinga', 'Ben&Ben'),
        ('Heavy', 'Linkin Park ft. Kiiara'),
        ('Innocence', 'Hildir Svensson and deprezz'),
        ('Numb', 'Linkin Park'),
        ('Breathe Me', 'Sia'),
        ('1-800-273-8255', 'Logic ft. Alessia Cara & Khalid'),
    ],
    'nostalgic': [
        ('Dati', 'Sam Concepcion'),
        ('Memories', 'Maroon 5'),
        ('Photograph', 'Ed Sheeran'),
        ('Photograph', 'Nickelback'),
        ('Ang Huling El Bimbo', 'Eraserheads'),
        ('7 Years', 'Lukas Graham'),
        ('Leaves', 'Ben&Ben'),
        ('See You Again', 'Wiz Khalifa ft. Charlie Puth'),
        ('When We Were Young', 'Adele'),
        ('Magbalik', 'Callalily'),
    ],
    'romantic': [
        ('Perfect', 'Ed Sheeran'),
        ('Photograph', 'Ed Sheeran'),
        ('Misteryoso', 'Cup of Joe'),
        ('Bibingka', 'Ben&Ben'),
        ('Chest Pain', 'Malcolm Todd'),
        ('A Thousand Years', 'Christina Perri'),
        ('On Bended Knee', 'Boyz II Men'),
        ('Blue', 'Yung Kai'),
        ("Can't Help Falling in Love", 'Elvis Presley'),
        ('Marilag', 'Dionela'),
    ],
    'lonely': [
        ('Iris', 'Goo Goo Dolls'),
        ('So Sick', 'Ne-Yo'),
        ('All By Myself', 'Céline Dion'),
        ('Always', 'Daniel Caesar'),
        ('Lonely', 'Justin Bieber & benny blanco'),
        ('Raining in Manila', 'Lola Amour'),
        ('Dancing on My Own', 'Robyn'),
        ('Sana', 'I Belong to the Zoo'),
        ('The A Team', 'Ed Sheeran'),
        ('Lonely', 'Akon'),
    ],
    'calm': [
        ('Tahanan', 'Adie'),
        ('Seasons', 'wave to earth'),
        ('Ocean Eyes', 'Billie Eilish'),
        ('Best Friend', 'Rex Orange County'),
        ('Weightless', 'Marconi Union'),
        ('Merry-Go-Round of Life', 'Joe Hisaishi'),
        ('Bloom', 'The Paper Kites'),
        ('Photograph', 'Ed Sheeran'),
        ('River Flows in You', 'Yiruma'),
        ('Bawat Daan', 'Ebe Dancel'),
    ],
    'stressed': [
        ('Under Pressure', 'Queen & David Bowie'),
        ('Heavy', 'Linkin Park ft. Kiiara'),
        ('Stressed Out', 'Twenty One Pilots'),
        ('Breathin', 'Ariana Grande'),
        ('Anxiety', 'Julia Michaels ft. Selena Gomez'),
        ('Pressure', 'Paramore'),
        ('Breathe Me', 'Sia'),
        ('In the End', 'Linkin Park'),
        ('No One Noticed', 'The Marías'),
        ('Everything I Wanted', 'Billie Eilish'),
    ],
    'surprising': [
        ('Suddenly I See', 'KT Tunstall'),
        ('Yellow', 'Coldplay'),
        ('A Sky Full of Stars', 'Coldplay'),
        ('Bawat Daan', 'Ebe Dancel'),
        ('Surprise Yourself', 'Jack Garratt'),
        ("You'll Be Safe Here", 'Rico Blanco'),
        ('Banana Pancakes', 'Jack Johnson'),
        ('Saturn', 'SZA'),
        ('The Greatest Show', 'Hugh Jackman & The Greatest Showman Ensemble'),
        ('Surprise', 'P!nk'),
    ],
}

MIX_SONGS = {
    'bittersweet': [
        ('The Day You Said Goodnight', 'Hale'),
        ('Married Life', 'Michael Giacchino'),
        ('Kathang Isip', 'Ben&Ben'),
        ('Multo', 'Cup of Joe'),
        ('Lifetime', 'Ben&Ben'),
    ],
    'tender': [
        ('Palagi', 'TJ Monterde'),
        ('Pasilyo', 'SunKissed Lola'),
        ('Tahanan', 'Adie'),
        ('Mahika', 'Adie & Janine Berdin'),
        ('Tadhana', 'Up Dharma Down'),
    ],
    'challenged': [
        ('Whatever It Takes', 'Imagine Dragons'),
        ('Karera', 'BINI'),
        ('The Climb', 'Miley Cyrus'),
        ('Unstoppable', 'Sia'),
        ('Hall of Fame', 'The Script ft. will.i.am'),
    ],
    'bittersweet_nostalgia': [
        ('The Nights', 'Avicii'),
        ('Castle on the Hill', 'Ed Sheeran'),
        ('Awit ng Barkada', 'APO Hiking Society'),
        ("Summer of '69", 'Bryan Adams'),
        ('Good Old Days', 'Macklemore ft. Kesha'),
    ],
    'romantic_melancholy': [
        ('Somebody Else', 'The 1975'),
        ('bittersweet', 'Madison Beer'),
        ('The Night We Met', 'Lord Huron'),
        ('Say You Love Me', 'Jessie Ware'),
        ('Happier', 'Marshmello & Bastille'),
    ],
}

# The lists as 0018 left them, for undoing.
PREVIOUS_EMOTION_SONGS = {
    'happy': [
        ('Happy', 'Pharrell Williams'),
        ("Can't Stop the Feeling!", 'Justin Timberlake'),
        ('Best Day of My Life', 'American Authors'),
        ('Shake It Off', 'Taylor Swift'),
        ('Paper Rings', 'Taylor Swift'),
        ('Salamin-Salamin', 'BINI'),
        ('Awitin Mo, Isasayaw ko', 'VST & Company'),
        ('Walking On Sunshine', 'Katrina & The Waves'),
        ("Don't Stop Me Now", 'Queen'),
        ('Ligaya', 'Eraserheads'),
    ],
    'sad': [
        ('Fix You', 'Coldplay'),
        ('Before It Sinks In', 'Moira Dela Torre'),
        ('Happier', 'Ed Sheeran'),
        ('The Night We Met', 'Lord Huron'),
        ('12:51', 'Krissy & Ericka'),
        ('Huling Sandali', 'December Avenue'),
        ("You'll Be in My Heart", 'NIKI'),
        ('Let Her Go', 'Passenger'),
        ('Blue', 'Yung Kai'),
        ('Paubaya', 'Moira Dela Torre'),
    ],
    'angry': [
        ('21 Guns', 'Green Day'),
        ('Look What You Made Me Do', 'Taylor Swift'),
        ('Nosi Ba Lasi', 'Sampaguita'),
        ('Cool Off', 'Yeng Constantino'),
        ('ERE', 'Juan Karlos'),
        ('You Oughta Know', 'Alanis Morissette'),
        ('Cartier Gucci Scarf', 'Young Thug'),
        ('Narda', 'Kamikazee'),
        ('Tatsulok', 'Bamboo'),
        ('Upuan', 'Gloc-9'),
    ],
    'motivational': [
        ('Fireflies', 'Owl City'),
        ('I Will Survive', 'Demi Lovato'),
        ('Araw-Araw', 'Ben&Ben'),
        ('Kiss It Better', 'Rihanna'),
        ('Dance All Night', 'ROSÉ'),
        ('Graduation March', 'Holiday Celebration Troupe'),
        ('Fight Song', 'Rachel Platten'),
        ('Feels', 'Calvin Harris'),
        ('Hall of Fame', 'The Script ft. will.i.am'),
        ('Believer', 'Imagine Dragons'),
    ],
    'fear': [
        ('Kathang Isip', 'Ben&Ben'),
        ('Creep', 'Radiohead'),
        ("Somebody's Watching Me", 'Rockwell'),
        ('No Surprises', 'Radiohead'),
        ('Roar', 'Katy Perry'),
        ('With a Smile', 'Eraserheads'),
        ("I'm Scared", 'Young Thug'),
        ('Battle Belongs', 'Phil Wickham'),
        ('The Hills', 'The Weeknd'),
        ('Huwag Kang Matakot', 'Reese Lansangan'),
    ],
    'depressing': [
        ('Fix You', 'Coldplay'),
        ('Leaves', 'Ben&Ben'),
        ('Somebody Else', 'The 1975'),
        ('505', 'Arctic Monkeys'),
        ('Pahinga', 'Ben&Ben'),
        ('From the Start', 'Laufey'),
        ('Valentine', 'Laufey'),
        ('With a Smile', 'Eraserheads'),
        ('1-800-273-8255', 'Logic ft. Alessia Cara & Khalid'),
        ('I Wanna Be Yours', 'Arctic Monkeys'),
    ],
    'nostalgic': [
        ('Dati', 'Sam Concepcion'),
        ('Memories', 'Maroon 5'),
        ('Photograph', 'Ed Sheeran'),
        ('Every Woman in the World', 'Air Supply'),
        ('Ang Huling El Bimbo', 'Eraserheads'),
        ('7 Years', 'Lukas Graham'),
        ('Perfect', 'Ed Sheeran'),
        ('Fireflies', 'Owl City'),
        ('Everybody Wants to Rule the World', 'Tears for Fears'),
        ('Magbalik', 'Callalily'),
    ],
    'romantic': [
        ('Perfect', 'Ed Sheeran'),
        ('Photograph', 'Ed Sheeran'),
        ('Misteryoso', 'Cup of Joe'),
        ('Bibingka', 'Ben&Ben'),
        ('Chest Pain', 'Malcolm Todd'),
        ('A Thousand Years', 'Christina Perri'),
        ('On Bended Knee', 'Boyz II Men'),
        ('Blue', 'Yung Kai'),
        ("Can't Help Falling in Love", 'Elvis Presley'),
        ('Feel It', 'Young Thug'),
    ],
    'lonely': [
        ('Iris', 'Goo Goo Dolls'),
        ('So Sick', 'Ne-Yo'),
        ('All By Myself', 'Céline Dion'),
        ('Always', 'Daniel Caesar'),
        ('Lonely', 'Justin Bieber & benny blanco'),
        ('Raining in Manila', 'Lola Amour'),
        ('Dancing on My Own', 'Robyn'),
        ('Sana', 'I Belong to the Zoo'),
        ("Kahit 'Di Mo Alam", 'South Border'),
        ('The A Team', 'Ed Sheeran'),
    ],
    'calm': [
        ('Blue', 'Yung Kai'),
        ('Seasons', 'wave to earth'),
        ('Ocean Eyes', 'Billie Eilish'),
        ('Best Friend', 'Rex Orange County'),
        ('Weightless', 'Marconi Union'),
        ('Merry-Go-Round of Life', 'Joe Hisaishi'),
        ('Leaves', 'Ben&Ben'),
        ('Bleeding Love', 'Leona Lewis'),
        ('River Flows in You', 'Yiruma'),
        ('Bawat Daan', 'Ebe Dancel'),
    ],
    'stressed': [
        ('Under Pressure', 'Queen & David Bowie'),
        ('We Belong Together', 'Mariah Carey'),
        ('Araw-Araw', 'Ben&Ben'),
        ('Leaves', 'Ben&Ben'),
        ('Night Dancer', 'imase'),
        ('Pressure', 'Paramore'),
        ('Stressed Out', 'Twenty One Pilots'),
        ('Hallelujah', 'Boyce Avenue'),
        ('No One Noticed', 'The Marías'),
        ('This Side of Paradise', 'Coyote Theory'),
    ],
    'surprising': [
        ('Bang Bang', 'Jessie J, Ariana Grande, Nicki Minaj'),
        ('Misteryoso', 'Cup of Joe'),
        ('Wake Me Up', 'Avicii'),
        ('Versace on the Floor', 'Bruno Mars'),
        ('All I Do Is Win', 'DJ Khaled'),
        ('Surprise Yourself', 'Jack Garratt'),
        ('Dynamite', 'BTS'),
        ("I'm Nilalamig", 'Cesca'),
        ('Ilaw sa Daan', 'IV of Spades'),
        ('Swizz Beatz', 'Young Thug'),
    ],
}

PREVIOUS_MIX_SONGS = {
    'bittersweet_nostalgia': [
        ('The Nights', 'Avicii'),
        ('Castle on the Hill', 'Ed Sheeran'),
        ('Kabisado', 'IV OF SPADES'),
        ('1990', 'Uncle Dags'),
        ('With a Smile', 'Eraserheads'),
    ],
}

def _set_list(links, owner_field, owner, songs, Song):
    """Make `owner`'s links exactly `songs`, in order; unlink everything else."""
    wanted = []
    for position, (title, artist) in enumerate(songs, start=1):
        wanted.append((Song.objects.get(title=title, artist=artist), position))
    links.filter(**{owner_field: owner}).exclude(
        song__in=[song for song, _ in wanted],
    ).delete()
    for song, position in wanted:
        link, created = links.get_or_create(
            **{owner_field: owner}, song=song, defaults={'position': position},
        )
        if not created and link.position != position:
            link.position = position
            link.save(update_fields=['position'])


def _set_lists(apps, emotion_songs, mix_songs):
    Song = apps.get_model('api', 'Song')
    Emotion = apps.get_model('api', 'Emotion')
    EmotionSong = apps.get_model('api', 'EmotionSong')
    EmotionPair = apps.get_model('api', 'EmotionPair')
    EmotionPairSong = apps.get_model('api', 'EmotionPairSong')
    for name, songs in emotion_songs.items():
        _set_list(EmotionSong.objects, 'emotion', Emotion.objects.get(name=name), songs, Song)
    for name, songs in mix_songs.items():
        _set_list(EmotionPairSong.objects, 'pair', EmotionPair.objects.get(name=name), songs, Song)


def sync_with_music_md(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    for data in NEW_SONGS:
        track_id = data['spotify_track_id']
        Song.objects.get_or_create(
            title=data['title'], artist=data['artist'],
            defaults={
                **data,
                'spotify_url': (
                    f'https://open.spotify.com/track/{track_id}' if track_id else None
                ),
            },
        )
    _set_lists(apps, EMOTION_SONGS, MIX_SONGS)


def restore_previous_lists(apps, schema_editor):
    Song = apps.get_model('api', 'Song')
    _set_lists(apps, PREVIOUS_EMOTION_SONGS, PREVIOUS_MIX_SONGS)
    for data in NEW_SONGS:
        # Only songs nothing uses any more: a later list may have linked one.
        Song.objects.filter(
            title=data['title'], artist=data['artist'],
            emotion_links__isnull=True, pair_links__isnull=True,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_mix_song_lists'),
    ]

    operations = [
        migrations.RunPython(sync_with_music_md, restore_previous_lists),
    ]
