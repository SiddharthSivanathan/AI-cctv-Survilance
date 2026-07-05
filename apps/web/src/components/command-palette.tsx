'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import { useTheme } from 'next-themes';
import {
  BarChart3,
  Bell,
  Camera,
  FileText,
  LayoutDashboard,
  Moon,
  Plus,
  Settings,
  SlidersHorizontal,
  Store,
} from 'lucide-react';
import { useCameras } from '@/features/cameras/hooks';
import { useStores } from '@/features/stores/hooks';

/** Global command palette (⌘K / Ctrl+K). Navigation, quick actions, search. */
export function CommandPalette() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);
  const cameras = useCameras();
  const stores = useStores();

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape') setOpen(false);
    };
    const onOpen = () => setOpen(true);
    document.addEventListener('keydown', onKey);
    window.addEventListener('visionops:command', onOpen);
    return () => {
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('visionops:command', onOpen);
    };
  }, []);

  const run = (action: () => void) => {
    setOpen(false);
    action();
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-[15vh]"
      onClick={() => setOpen(false)}
    >
      <div className="w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
        <Command className="overflow-hidden rounded-xl border bg-background shadow-2xl" loop>
          <Command.Input
            autoFocus
            placeholder="Type a command or search…"
            className="w-full border-b bg-transparent px-4 py-3 text-sm outline-none placeholder:text-muted-foreground"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="px-3 py-6 text-center text-sm text-muted-foreground">
              No results.
            </Command.Empty>

            <Group heading="Navigation">
              <Item icon={LayoutDashboard} onSelect={() => run(() => router.push('/dashboard'))}>
                Dashboard
              </Item>
              <Item icon={Store} onSelect={() => run(() => router.push('/stores'))}>
                Stores
              </Item>
              <Item icon={Camera} onSelect={() => run(() => router.push('/cameras'))}>
                Cameras
              </Item>
              <Item icon={Bell} onSelect={() => run(() => router.push('/alerts'))}>
                Alerts
              </Item>
              <Item icon={FileText} onSelect={() => run(() => router.push('/events'))}>
                Events
              </Item>
              <Item icon={SlidersHorizontal} onSelect={() => run(() => router.push('/rules'))}>
                Rules
              </Item>
              <Item icon={BarChart3} onSelect={() => run(() => router.push('/dashboard'))}>
                Analytics
              </Item>
              <Item icon={Settings} onSelect={() => run(() => router.push('/settings'))}>
                Settings
              </Item>
            </Group>

            <Group heading="Quick actions">
              <Item icon={Plus} onSelect={() => run(() => router.push('/cameras/new'))}>
                Add camera
              </Item>
              <Item icon={Plus} onSelect={() => run(() => router.push('/stores/new'))}>
                Add store
              </Item>
              <Item
                icon={Moon}
                onSelect={() => run(() => setTheme(theme === 'dark' ? 'light' : 'dark'))}
              >
                Toggle dark mode
              </Item>
            </Group>

            {(cameras.data?.length ?? 0) > 0 && (
              <Group heading="Cameras">
                {cameras.data?.map((c) => (
                  <Item
                    key={c.id}
                    icon={Camera}
                    value={`camera ${c.name}`}
                    onSelect={() => run(() => router.push(`/cameras/${c.id}`))}
                  >
                    {c.name}
                  </Item>
                ))}
              </Group>
            )}

            {(stores.data?.length ?? 0) > 0 && (
              <Group heading="Stores">
                {stores.data?.map((s) => (
                  <Item
                    key={s.id}
                    icon={Store}
                    value={`store ${s.name}`}
                    onSelect={() => run(() => router.push(`/stores/${s.id}`))}
                  >
                    {s.name}
                  </Item>
                ))}
              </Group>
            )}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}

function Group({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <Command.Group
      heading={heading}
      className="px-1 py-1 text-xs font-medium text-muted-foreground [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
    >
      {children}
    </Command.Group>
  );
}

function Item({
  icon: Icon,
  children,
  onSelect,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
  onSelect: () => void;
  value?: string;
}) {
  return (
    <Command.Item
      value={value ?? (typeof children === 'string' ? children : undefined)}
      onSelect={onSelect}
      className="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm text-foreground aria-selected:bg-accent aria-selected:text-accent-foreground"
    >
      <Icon className="h-4 w-4 text-muted-foreground" />
      {children}
    </Command.Item>
  );
}
