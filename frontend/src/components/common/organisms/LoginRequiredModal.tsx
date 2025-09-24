import { useNavigate } from '@tanstack/react-router';
import { Typography } from '../atoms/Typography';
import { Button } from '../atoms/Button';
import { useModalStore } from '../../../stores/useModalStore';
import lockImage from '../../../assets/img/lock.png?format=webp&quality=80';

export function LoginRequiredModal() {
  const navigate = useNavigate();
  const { showLoginModal, modalMessage, redirectPath, clearModal } = useModalStore();

  const handleLoginClick = () => {
    // 로그인 페이지로 이동하기 전에 리다이렉트 경로를 sessionStorage에 저장
    if (redirectPath) {
      sessionStorage.setItem('post_login_redirect', redirectPath);
    }
    clearModal();
    navigate({ to: '/login' });
  };

  const handleCloseClick = () => {
    clearModal();
  };

  if (!showLoginModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 오버레이 배경 */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={handleCloseClick} />

      {/* 모달 컨텐츠 */}
      <div className="relative bg-white rounded-2xl shadow-2xl p-8 mx-4 max-w-md w-full animate-in fade-in slide-in-from-bottom-3 duration-300">
        {/* 자물쇠 이미지 */}
        <div className="flex justify-center mb-6">
          <img src={lockImage} alt="자물쇠" className="w-20 h-20 object-contain" />
        </div>

        {/* 제목 */}
        <Typography as="h2" variant="title" weight="bold" align="center" className="mb-4">
          로그인이 필요합니다
        </Typography>

        {/* 메시지 */}
        <Typography variant="default" color="gray" align="center" className="mb-8">
          {modalMessage}
        </Typography>

        {/* 버튼들 */}
        <div className="flex gap-3">
          <Button
            variant="outlined"
            size="lg"
            onClick={handleCloseClick}
            className="flex-1 font-semibold"
          >
            취소
          </Button>

          <Button
            variant="contained"
            size="lg"
            onClick={handleLoginClick}
            className="flex-1 font-semibold"
          >
            로그인하기
          </Button>
        </div>
      </div>
    </div>
  );
}
