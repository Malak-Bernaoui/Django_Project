import random
import urllib.request
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from PIL import Image

from posts.models import Post

User = get_user_model()

DEMO_ACCOUNTS = [
    ('demo_alice', 'Alice', 'Travel & photography enthusiast'),
    ('demo_bob', 'Bob', 'Fitness coach and foodie'),
    ('demo_charlie', 'Charlie', 'Digital artist and designer'),
    ('demo_diana', 'Diana', 'Music lover and DJ'),
    ('demo_evan', 'Evan', 'Tech and coding daily'),
    ('demo_fiona', 'Fiona', 'Fashion and lifestyle'),
    ('demo_george', 'George', 'Nature and wildlife shots'),
    ('demo_helen', 'Helen', 'Books, coffee, and cats'),
]


def download_image(seed, size=(600, 600)):
    url = f'https://picsum.photos/seed/{seed}/{size[0]}/{size[1]}'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    img = Image.open(BytesIO(data))
    if img.mode not in ('RGB', 'L'):
        img = img.convert('RGB')
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()


class Command(BaseCommand):
    help = 'Create demo accounts with profile pictures and random posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--posts-per-user',
            type=int,
            default=6,
            help='Number of posts to create per demo account (default: 6)',
        )

    def handle(self, *args, **options):
        posts_per_user = options['posts_per_user']
        created_users = 0
        created_posts = 0

        for username, first_name, bio in DEMO_ACCOUNTS:
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'bio': bio,
                    'is_private': False,
                },
            )
            if user_created:
                user.set_password('demo1234')
                user.save()
                created_users += 1
                self.stdout.write(self.style.SUCCESS(f'Created user @{username}'))
            else:
                if not user.bio:
                    user.bio = bio
                    user.save(update_fields=['bio'])

            if not user.profile_picture or 'default' in str(user.profile_picture):
                try:
                    avatar_bytes = download_image(f'avatar_{username}', (200, 200))
                    user.profile_picture.save(
                        f'{username}_avatar.jpg',
                        ContentFile(avatar_bytes),
                        save=True,
                    )
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f'Avatar skipped for {username}: {exc}'))

            existing_posts = user.posts.count()
            posts_to_create = max(0, posts_per_user - existing_posts)
            captions = [
                'Beautiful day!',
                'New adventure unlocked.',
                'Loving this moment.',
                'Weekend vibes.',
                'Can\'t stop exploring.',
                'Good times with great people.',
                'Sunset mood.',
                'Making memories.',
            ]

            for i in range(posts_to_create):
                seed = f'{username}_post_{user.posts.count() + i}'
                try:
                    image_bytes = download_image(seed)
                    post = Post(
                        author=user,
                        caption=random.choice(captions),
                        likes_count=random.randint(5, 120),
                        comments_count=random.randint(0, 25),
                    )
                    post.image.save(f'{seed}.jpg', ContentFile(image_bytes), save=False)
                    post.save()
                    created_posts += 1
                except Exception as exc:
                    self.stdout.write(self.style.WARNING(f'Post skipped for {username}: {exc}'))

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Users created: {created_users}, posts created: {created_posts}.'
            )
        )
