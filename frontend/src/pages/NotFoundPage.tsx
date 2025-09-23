import { Typography } from '@/components/common/atoms/Typography';
import errorImage from '@/assets/img/error404.png?format=webp&quality=80';

const NotFoundPage = () => {
  return (
    <div className="flex-1 flex items-center justify-center bg-gray-50">
      <div className="text-center px-4">
        <img src={errorImage} alt="404 에러" className="w-auto h-64 mx-auto" />

        <Typography className="text-6xl mb-4" weight="bold" align="center">
          404
        </Typography>

        <Typography as="h2" variant="title" weight="semibold" align="center" className="mb-4">
          페이지를 찾을 수 없습니다
        </Typography>

        <Typography variant="default" color="gray" align="center" className="mb-8 max-w-md mx-auto">
          요청하신 페이지가 존재하지 않거나 이동되었을 수 있습니다.
        </Typography>
      </div>
    </div>
  );
};

export default NotFoundPage;
