FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package*.json ./
<<<<<<< HEAD
RUN npm ci
=======
RUN npm ci --only=production
>>>>>>> bc57f41 (Initial CAR-BOOKING project)

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

<<<<<<< HEAD
# ==================== เพิ่มส่วนนี้เข้ามา ====================
# รับค่า Build Arguments จาก Docker Compose / Coolify
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# ========================================================

# เพิ่ม Memory ให้ Node.js กัน Webpack Out of Memory
ENV NODE_OPTIONS="--max-old-space-size=2048"

=======
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

<<<<<<< HEAD
CMD ["node", "server.js"]
=======
CMD ["node", "server.js"]
>>>>>>> bc57f41 (Initial CAR-BOOKING project)
