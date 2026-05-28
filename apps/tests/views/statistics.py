from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Count
from ..models import UserTestResult, SpeakingResult, Section


class BandScoreHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        writing_results = UserTestResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).order_by('created_at').values('band_score', 'created_at', 'test__title')

        speaking_results = SpeakingResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).order_by('created_at').values('band_score', 'created_at', 'test__title')

        return Response({
            'writing': list(writing_results),
            'speaking': list(speaking_results),
        })


class OverallProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        writing_stats = UserTestResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).aggregate(
            average=Avg('band_score'),
            total=Count('id')
        )

        speaking_stats = SpeakingResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).aggregate(
            average=Avg('band_score'),
            total=Count('id')
        )

        return Response({
            'writing': {
                'average_band_score': round(writing_stats['average'] or 0, 1),
                'total_tests': writing_stats['total'],
            },
            'speaking': {
                'average_band_score': round(speaking_stats['average'] or 0, 1),
                'total_tests': speaking_stats['total'],
            },
        })


class WeakAreasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        writing_avg = UserTestResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).aggregate(avg=Avg('band_score'))['avg'] or 0

        speaking_avg = SpeakingResult.objects.filter(
            user=request.user,
            band_score__isnull=False
        ).aggregate(avg=Avg('band_score'))['avg'] or 0

        areas = [
            {'section': 'writing', 'average_band_score': round(writing_avg, 1)},
            {'section': 'speaking', 'average_band_score': round(speaking_avg, 1)},
        ]

        weak_areas = [a for a in areas if a['average_band_score'] < 6.0]
        weak_areas.sort(key=lambda x: x['average_band_score'])

        return Response({
            'weak_areas': weak_areas,
            'all_areas': areas,
        })