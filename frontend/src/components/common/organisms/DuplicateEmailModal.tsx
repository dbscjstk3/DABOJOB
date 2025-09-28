import { Typography } from '../atoms/Typography';
import { Button } from '../atoms/Button';
import { useModalStore } from '../../../stores/useModalStore';
import lockImage from '../../../assets/img/lock.png?format=webp&quality=80';

export function DuplicateEmailModal() {
  const { showDuplicateEmailModal, duplicateEmailMessage, closeDuplicateEmailModal } = useModalStore();

  const handleCloseClick = () => {
    closeDuplicateEmailModal();
  };

  if (!showDuplicateEmailModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-md rounded-2xl bg-white p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-3 duration-200">
        {/* 아이콘 */}
        <div className="mb-6 flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center">
            <img 
              src={lockImage} 
              alt="Error" 
              className="h-20 w-20 object-contain"
            />
          </div>
        </div>

        {/* 메시지 */}
        <div className="mb-8 text-center">
          <Typography as="h2" variant="title" weight="bold" align="center" className="mb-3 text-slate-900">
            이메일 중복 오류
          </Typography>
          <Typography variant="default" color="gray" className="leading-relaxed">
            {duplicateEmailMessage}
          </Typography>
        </div>

        {/* 버튼 */}
        <div className="flex justify-center">
          <Button
            variant="contained"
            size="lg"
            onClick={handleCloseClick}
            className="w-full text-white focus:ring-red-500"
          >
            <Typography variant="default" weight="semibold">
              확인
            </Typography>
          </Button>
        </div>
      </div>
    </div>
  );
}
