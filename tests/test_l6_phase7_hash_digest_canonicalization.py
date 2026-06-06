from tiangong_kernel.l6_plugins.adaptive_collaboration import LearningNeedReviewRequest

def test_hash_digest_canonicalization():
    assert LearningNeedReviewRequest().digest == LearningNeedReviewRequest().digest
