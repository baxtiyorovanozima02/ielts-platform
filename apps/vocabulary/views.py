from datetime import datetime, timezone
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Word, WordReview
from .serializers import WordSerializer, WordReviewSerializer


class WordListCreateView(generics.ListCreateAPIView):
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="So'zlar ro'yxati")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Yangi so'z qo'shish")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Word.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WordSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="So'z tafsiloti")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="So'zni yangilash")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="So'zni o'chirish")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Word.objects.filter(user=self.request.user)


class DueWordsView(generics.ListAPIView):
    serializer_class = WordReviewSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(operation_summary="Takrorlash kerak bo'lgan so'zlar")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        now = datetime.now(timezone.utc)
        return WordReview.objects.filter(
            user=self.request.user,
            next_review__lte=now
        ).select_related('word').order_by('next_review')


class WordReviewView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="So'zni baholash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['word_id', 'quality'],
            properties={
                'word_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quality': openapi.Schema(type=openapi.TYPE_INTEGER, description='0-3 orasida'),
            }
        )
    )
    def post(self, request):
        word_id = request.data.get('word_id')
        quality = request.data.get('quality')

        if quality is None or not (0 <= int(quality) <= 3):
            return Response({'error': 'quality 0-3 orasida bo\'lishi kerak'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            word = Word.objects.get(id=word_id, user=request.user)
        except Word.DoesNotExist:
            return Response({'error': 'So\'z topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        quality = int(quality)
        review = WordReview.objects.filter(user=request.user, word=word).last()

        if review:
            repetitions = review.repetitions
            ease_factor = review.ease_factor
            interval = review.interval
        else:
            repetitions = 0
            ease_factor = 2.5
            interval = 1

        if quality >= 2:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease_factor)
            repetitions += 1
        else:
            repetitions = 0
            interval = 1

        ease_factor = max(1.3, ease_factor + 0.1 - (3 - quality) * (0.08 + (3 - quality) * 0.02))

        from datetime import timedelta
        next_review = datetime.now(timezone.utc) + timedelta(days=interval)

        WordReview.objects.create(
            user=request.user,
            word=word,
            quality=quality,
            next_review=next_review,
            interval=interval,
            repetitions=repetitions,
            ease_factor=ease_factor
        )

        return Response({
            'word': word.word,
            'next_review': next_review,
            'interval_days': interval,
        }, status=status.HTTP_201_CREATED)