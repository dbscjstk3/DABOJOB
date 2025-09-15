import { Link, useNavigate } from '@tanstack/react-router';
import { SearchBox } from '../molecules/SearchBox';
import { Button } from '../atoms/Button';

import DABOJOB_logo from '@/assets/logo/DABOJOB_logo_loop3.gif';

type User = { name: string };

type HeaderProps = {
  user?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;

  fetchSuggestions: (
    q: string,
    signal?: AbortSignal,
  ) => Promise<{ id: string | number; label: string }[]>;
  onSelectSuggestion?: (item: { id: string | number; label: string }) => void;
  onSubmitSearch?: (query: string) => void;
};

export function Header({
  user,
  onLogin,
  onLogout,
  fetchSuggestions,
  onSelectSuggestion,
  onSubmitSearch,
}: HeaderProps) {
  const navigate = useNavigate();

  return (
    <header
      className="
        sticky top-0 z-50 border-b
        bg-white/80 backdrop-blur
        supports-[backdrop-filter]:bg-white/60
      "
    >
      <div className="w-full px-4 py-3 md:px-8 md:py-4 lg:px-16 lg:py-6">
        <div className="flex flex-col gap-3 md:flex-row md:gap-0 md:h-8 md:items-center">
          {/* 모바일: 첫 번째 줄 / 태블릿+: 전체 레이아웃 */}
          <div className="flex items-center justify-between md:justify-start md:gap-6 lg:gap-8 md:w-full">
            <Logo />

            {/* 태블릿+ 검색창 */}
            <div className="hidden md:block md:w-[300px] lg:w-[500px] xl:w-[700px]">
              <SearchBox
                fetchSuggestions={fetchSuggestions}
                onSelect={onSelectSuggestion}
                onSubmit={onSubmitSearch}
                className="w-full"
              />
            </div>

            {/* 로그인/로그아웃 버튼 */}
            <div className="md:ml-auto">
              <UserArea
                user={user}
                onLogin={() => {
                  onLogin?.();
                  navigate({ to: '/login' });
                }}
                onLogout={onLogout}
              />
            </div>
          </div>

          {/* 모바일: 두 번째 줄 (검색창) */}
          <div className="block md:hidden w-full">
            <SearchBox
              fetchSuggestions={fetchSuggestions}
              onSelect={onSelectSuggestion}
              onSubmit={onSubmitSearch}
              className="w-full"
            />
          </div>
        </div>
      </div>
    </header>
  );
}

function Logo() {
  return (
    <Link to="/" aria-label="홈으로 이동" className="flex items-center gap-2 shrink-0">
      <img
        src={DABOJOB_logo}
        alt="DABOJOB : ) 다보자"
        className="h-6 md:h-7 lg:h-7 w-auto"
        draggable={false}
      />
    </Link>
  );
}

function UserArea({
  user,
  onLogin,
  onLogout,
}: {
  user?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;
}) {
  return (
    <div className="flex items-center gap-3 shrink-0">
      {user ? (
        <>
          <span className="hidden sm:block text-sm text-slate-600 max-w-[140px] truncate -ml-1">
            {user.name}님 반가워요!
          </span>
          <Button variant="contained" size="sm" onClick={onLogout} aria-label="로그아웃">
            로그아웃
          </Button>
        </>
      ) : (
        <Button variant="contained" size="md" onClick={onLogin} aria-label="로그인">
          로그인
        </Button>
      )}
    </div>
  );
}
